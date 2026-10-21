import hashlib
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .validation import DataError, clean_json


class ModelService:
    """One fitted preprocessing/model contract for all inference entry points."""
    def __init__(self, root):
        self.root = Path(root)
        self.model = self.preprocessor = None
        self.features = []
        self.error = self.version = None
        self._reference = None
        try:
            prep_path = self.root / "artifacts/preprocessor.joblib"
            model_path = self.root / "artifacts/baseline_model.joblib"
            prep = joblib.load(prep_path)
            self.model = joblib.load(model_path)
            self.preprocessor = prep["preprocessor"]
            self.features = list(prep["valid_features"])
            # Compatibility patch for SimpleImputer across scikit-learn versions (e.g. _fill_dtype)
            if hasattr(self.preprocessor, "named_steps"):
                for step in self.preprocessor.named_steps.values():
                    if hasattr(step, "statistics_") and not hasattr(step, "_fill_dtype"):
                        step._fill_dtype = getattr(step.statistics_, "dtype", np.dtype("float64"))
            elif hasattr(self.preprocessor, "statistics_") and not hasattr(self.preprocessor, "_fill_dtype"):
                self.preprocessor._fill_dtype = getattr(self.preprocessor.statistics_, "dtype", np.dtype("float64"))
            self.version = hashlib.sha256(prep_path.read_bytes() + model_path.read_bytes()).hexdigest()[:20]
        except Exception as exc:
            self.model = None
            self.error = f"모델을 불러올 수 없습니다 ({type(exc).__name__}: {exc})."

    def predict(self, df):
        if self.model is None:
            raise RuntimeError(self.error)
        missing = sorted(set(self.features) - set(df.columns))
        if missing:
            raise DataError(f"예측 필수 센서 열 {len(missing)}개가 없습니다. 예: {', '.join(missing[:12])}")
        scaled = self.preprocessor.transform(df[self.features])
        scores = np.asarray(self.model.predict_proba(scaled))[:, 1]
        if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
            raise RuntimeError("모델이 유효하지 않은 위험 점수를 반환했습니다.")
        result = df[["row_id", "sample_id"]].copy()
        result["risk_score"] = scores
        result["abnormal_sensor_count"] = (np.abs(scaled) > 2).sum(axis=1)
        result = result.sort_values(["risk_score", "row_id"], ascending=[False, True], kind="stable")
        result["risk_rank"] = np.arange(1, len(result) + 1)
        result["is_top20_review"] = result.risk_rank <= int(np.ceil(len(result) * .2))
        return result.reset_index(drop=True)

    def reference(self):
        if self._reference is None:
            train = pd.read_csv(self.root / "artifacts/train_indices.csv")
            raw = pd.read_csv(self.root / "data/processed/secom_features.csv")
            ids = train.loc[train.label == 0, "sample_id"]
            self._reference = raw.loc[raw.sample_id.isin(ids), self.features].copy()
        return self._reference

    def _shap_values(self, frame, model_version):
        if model_version != self.version:
            raise DataError("이 데이터셋의 모델 버전과 현재 모델이 달라 SHAP을 계산할 수 없습니다.")
        import shap
        scaled = self.preprocessor.transform(frame[self.features])
        inner = getattr(self.model, "lgbm_model", self.model)
        names = list(self.features)
        if hasattr(self.model, "lgbm_model"):
            values = np.hstack([scaled, (np.abs(scaled) > 2).sum(axis=1, keepdims=True)])
            names.append("abnormal_sensor_count")
        else:
            values = scaled
        explainer = shap.TreeExplainer(inner)
        sv = explainer.shap_values(values)
        if isinstance(sv, list):
            sv = sv[-1]
        sv = np.asarray(sv)
        if sv.ndim == 3:
            sv = sv[:, :, -1]
        if sv.shape != (len(frame), len(names)):
            raise RuntimeError("SHAP 피처 수가 모델 입력과 다릅니다.")
        base = np.asarray(explainer.expected_value).reshape(-1)[-1]
        return names, values, sv, float(base)

    def explain(self, frame, row_id, model_version):
        row = frame.loc[frame.row_id == row_id]
        if len(row) != 1:
            raise DataError("해당 row_id를 찾을 수 없습니다.")
        names, values, matrix, base = self._shap_values(row, model_version)
        sv = matrix[0]
        order = np.argsort(-np.abs(sv))[:15]
        records = [{"feature": names[i], "shap": float(sv[i]), "model_input": float(values[0, i])} for i in order]
        running = base
        waterfall = []
        for r in records:
            waterfall.append({**r, "start": running, "end": running+r['shap']})
            running += r['shap']
        other = float(sv.sum()-sum(r['shap'] for r in records))
        waterfall.append({"feature": f"나머지 {len(names)-len(records)}개 피처", "shap": other,
                          "start": running, "end": running+other})
        return clean_json({"row_id": row_id, "sample_id": row.iloc[0].sample_id,
                           "risk_score": row.iloc[0].risk_score, "base_value": float(base),
                           "sum_all_shap": float(sv.sum()), "model_raw_output": float(base + sv.sum()),
                           "units": "model raw output (binary LightGBM: log-odds)",
                           "rows": records, "waterfall": waterfall, "feature_count":len(names),
                           "risk_increase": [{"feature": names[i], "shap": float(sv[i])} for i in np.argsort(-sv) if sv[i]>0][:5],
                           "risk_decrease": [{"feature": names[i], "shap": float(sv[i])} for i in np.argsort(sv) if sv[i]<0][:5],
                           "base_risk_score": float(1/(1+np.exp(-base))),
                           "reconstructed_risk_score": float(1/(1+np.exp(-(base+sv.sum())))),
                           "note": "모델 예측의 기여도이며 실제 고장 원인을 확정하지 않습니다."})

    def global_explain(self, frame, model_version, limit=15, max_samples=200):
        ordered = frame.sort_values('row_id')
        positions = np.linspace(0, len(ordered)-1, min(max_samples,len(ordered)), dtype=int)
        selected = ordered.iloc[positions]
        names, _, values, _ = self._shap_values(selected,model_version)
        importance = np.mean(np.abs(values),axis=0)
        order = np.argsort(-importance)[:limit]
        return clean_json({"scope_count":len(frame),"analyzed_count":len(selected),
            "sampling":"전체 표본" if len(selected)==len(frame) else "원본 행 순서에서 균등 간격 표본 선택",
            "rows":[{"feature":names[i],"mean_abs_shap":float(importance[i]),"rank":rank} for rank,i in enumerate(order,1)],
            "note":"평균 절대 SHAP은 모델 영향도이며 고장 원인이나 인과 효과가 아닙니다."})
