"""Reusable analysis tools: all statistics are computed from actual dataframe rows."""
import inspect
import math

import numpy as np
import pandas as pd

from .validation import DataError, clean_json


TOOL_DESCRIPTIONS = {
    "profile_dataset": "데이터 크기, 결측·상수 센서, 정답 라벨과 위험 점수 분포를 확인합니다.",
    "rank_samples": "위험 점수로 정렬한 실제 표본과 선택 센서값을 조회합니다.",
    "query_data": "조건 필터, 컬럼 선택, 정렬과 그룹 집계를 조합합니다. 전체 행을 계산하고 반환 표만 제한합니다.",
    "compare_groups": "위험 점수 상위 검토 비율과 나머지 센서의 평균·표준화 차이를 비교합니다.",
    "correlate": "선택 숫자 열과 대상 열의 Pearson/Spearman 상관 및 유효 표본 수를 계산합니다.",
    "time_summary": "실제 timestamp의 일·주·월별 표본 수, 평균 위험 점수, 확인 라벨 불량률을 계산합니다.",
    "compare_reference": "해당 모델의 학습 기준 정상군(Baseline Reference)과 업로드 센서 분포를 비교합니다.",
    "evaluate_predictions": "정답이 모두 있는 데이터셋에서 상위 검토 비율의 혼동행렬·Recall·Precision·Lift를 계산합니다.",
    "explain_sample": "row_id 표본을 실제 모델 TreeExplainer로 설명합니다. 실제 고장 원인을 확정하지 않습니다.",
    "diagnose_sample": "sample_id 표본의 순위·TP/FP/FN/TN, 정상군 대비 Top 5 센서·상태, 실제 SHAP 워터폴과 근거별 검토 권고를 함께 계산합니다.",
    "sensor_drift": "실제 경과 시간으로 Pearson·Kendall·표준화 기울기·초기후기 이동과 종합 드리프트 지수를 계산하고 상승·하강을 구분합니다.",
    "global_shap": "선택 데이터셋의 평균 절대 SHAP 센서 중요도를 계산합니다. 큰 데이터는 원본 행 순서로 균등 표본을 선택하고 분석 수를 명시합니다.",
}


def chart(title, x, y, kind="bar"):
    return {"data": [{"type": "scatter" if kind == "line" else kind, "x": x, "y": y,
                      **({"mode": "lines+markers"} if kind == "line" else {})}],
            "layout": {"title": title, "margin": {"t": 55, "b": 90, "l": 60, "r": 20}}}


def ratio_value(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not .01 <= value <= .5:
        raise DataError("review_ratio는 0.01~0.5 사이 숫자여야 합니다.")
    return float(value)


def limit_value(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 50:
        raise DataError("limit은 1~50 정수여야 합니다.")
    return value


class AnalysisTools:
    def __init__(self, metadata, raw, predictions, model_service):
        self.metadata = metadata
        self.raw = raw
        self.model = model_service
        # Predictions are score-sorted; positional concat would silently attach wrong sensors.
        self.frame = raw.merge(predictions.drop(columns=["sample_id"]), on="row_id", validate="one_to_one")
        self.sensors = [c for c in raw if c.startswith("feature_")]

    def columns(self, values, default=None, numeric=True):
        cols = default if values is None else values
        if not isinstance(cols, list) or not 1 <= len(cols) <= 20 or not all(isinstance(c, str) for c in cols):
            raise DataError("columns는 1~20개 컬럼명 목록이어야 합니다.")
        unknown = set(cols) - set(self.frame.columns)
        if unknown:
            raise DataError("없는 컬럼: " + ", ".join(sorted(unknown)))
        if numeric and any(not pd.api.types.is_numeric_dtype(self.frame[c]) for c in cols):
            raise DataError("숫자 컬럼을 선택해 주세요.")
        return list(dict.fromkeys(cols))

    def execute(self, name, arguments=None):
        if name not in TOOL_DESCRIPTIONS:
            raise DataError("등록되지 않은 분석 Tool입니다.")
        if arguments is not None and not isinstance(arguments, dict):
            raise DataError("Tool 인자는 JSON 객체여야 합니다.")
        fn = getattr(self, name)
        try:
            inspect.signature(fn).bind(**(arguments or {}))
        except TypeError as exc:
            raise DataError(str(exc)) from exc
        result = fn(**(arguments or {}))
        return clean_json({"tool": name, "dataset_id": self.metadata["dataset_id"],
                           "model_version": self.metadata["model_version"], "scope_count": len(self.frame),
                           "data": result})

    def profile_dataset(self):
        sensors = self.raw[self.sensors]
        missing = sensors.isna().sum().sort_values(ascending=False)
        top = [{"sensor": c, "missing_count": int(v), "missing_ratio": float(v / len(sensors))}
               for c, v in missing.head(15).items() if v > 0]
        labels = self.frame.get("actual_label", pd.Series(np.nan, index=self.frame.index))
        known = int(labels.notna().sum())
        result = {"row_count": len(self.frame), "sensor_count": len(self.sensors),
                  "columns": list(self.frame.columns), "missing_cells": int(sensors.isna().sum().sum()),
                  "missing_ratio": float(sensors.isna().mean().mean()), "top_missing_sensors": top,
                  "constant_sensors": [c for c in self.sensors if sensors[c].nunique(dropna=True) == 1],
                  "all_missing_sensors": [c for c in self.sensors if sensors[c].notna().sum() == 0],
                  "known_label_count": known, "unknown_label_count": len(labels) - known,
                  "confirmed_failures": int((labels == 1).sum()) if known else None,
                  "confirmed_failure_rate": float((labels == 1).sum() / known) if known else None,
                  "risk_score": self.frame.risk_score.describe(percentiles=[.1, .5, .9]).to_dict(),
                  "charts": [chart("결측 센서 상위 항목", [r["sensor"] for r in top], [r["missing_count"] for r in top])]}
        return result

    def rank_samples(self, limit=10, direction="descending", columns=None):
        limit_value(limit)
        if direction not in ["ascending", "descending"]:
            raise DataError("direction은 ascending 또는 descending이어야 합니다.")
        cols = self.columns(columns, self.sensors[:5])
        selected = list(dict.fromkeys(["row_id", "sample_id", "risk_score", "risk_rank", "is_top20_review"] +
                                    (["actual_label"] if "actual_label" in self.frame else []) + cols))
        ranked = self.frame.sort_values(["risk_score", "row_id"], ascending=[direction == "ascending", True])
        return {"rows": ranked[selected].head(limit).to_dict("records"), "total_rows": len(ranked)}

    def query_data(self, columns=None, filters=None, group_by=None, aggregations=None,
                   sort_by=None, descending=True, limit=20):
        limit_value(limit)
        if not isinstance(descending, bool):
            raise DataError("descending은 boolean이어야 합니다.")
        frame = self.frame.copy()
        if filters is not None and (not isinstance(filters, list) or len(filters) > 10):
            raise DataError("필터는 10개 이하의 목록이어야 합니다.")
        for condition in filters or []:
            if not isinstance(condition, dict) or set(condition) != {"column", "op", "value"}:
                raise DataError("필터는 column, op, value를 포함해야 합니다.")
            c, op, value = condition["column"], condition["op"], condition["value"]
            self.columns([c], numeric=False)
            series = frame[c]
            if op in ["is_missing", "not_missing"]:
                mask = series.isna() if op == "is_missing" else series.notna()
            else:
                if isinstance(value, (dict, list)) or value is None:
                    raise DataError("비교값은 숫자·문자열·boolean이어야 합니다.")
                if pd.api.types.is_numeric_dtype(series):
                    if isinstance(value, bool) and not pd.api.types.is_bool_dtype(series):
                        raise DataError("숫자 조건에는 숫자 비교값이 필요합니다.")
                    try:
                        value = float(value)
                        if not math.isfinite(value): raise ValueError()
                    except (ValueError, TypeError) as exc:
                        raise DataError("숫자 조건에는 유한 숫자 비교값이 필요합니다.") from exc
                operations = {"eq": series.eq, "ne": series.ne, "gt": series.gt,
                              "ge": series.ge, "lt": series.lt, "le": series.le}
                if op not in operations:
                    raise DataError("지원하지 않는 필터 연산입니다.")
                try:
                    mask = operations[op](value)
                except TypeError as exc:
                    raise DataError("필터 값의 자료형이 컬럼과 맞지 않습니다.") from exc
            frame = frame.loc[mask.fillna(False)]
        filtered_count = len(frame)
        if aggregations:
            if not isinstance(aggregations, list) or len(aggregations) > 10:
                raise DataError("집계는 1~10개여야 합니다.")
            spec = {}
            for a in aggregations:
                if not isinstance(a, dict) or set(a) != {"column", "op"}:
                    raise DataError("집계는 column과 op를 포함해야 합니다.")
                c, op = a["column"], a["op"]
                self.columns([c], numeric=op not in ["count", "nunique"])
                if op not in ["count", "nunique", "mean", "median", "std", "min", "max", "sum"]:
                    raise DataError("지원하지 않는 집계 연산입니다.")
                spec[f"{c}__{op}"] = pd.NamedAgg(column=c, aggfunc=op)
            if group_by:
                groups = self.columns(group_by, numeric=False)
                if len(groups) > 3:
                    raise DataError("그룹 컬럼은 최대 3개입니다.")
                frame = frame.groupby(groups, dropna=False).agg(**spec).reset_index()
            else:
                frame = pd.DataFrame([{name: self._aggregate(frame[agg.column], agg.aggfunc) for name, agg in spec.items()}])
        elif group_by:
            raise DataError("그룹 분석에는 aggregations가 필요합니다.")
        else:
            defaults = [c for c in ["row_id", "sample_id", "timestamp", "risk_score", "risk_rank", "actual_label"] if c in frame]
            frame = frame[self.columns(columns, defaults, numeric=False)]
        if sort_by is not None:
            if sort_by not in frame:
                raise DataError("정렬 컬럼이 결과에 없습니다.")
            frame = frame.sort_values(sort_by, ascending=not descending, kind="stable")
        return {"filtered_rows": filtered_count, "result_rows": len(frame), "rows": frame.head(limit).to_dict("records"), "truncated": len(frame) > limit}

    @staticmethod
    def _aggregate(series, op):
        return getattr(series, op)()

    def compare_groups(self, review_ratio=.2, columns=None):
        ratio = ratio_value(review_ratio)
        ranked = self.frame.sort_values(["risk_score", "row_id"], ascending=[False, True])
        k = int(math.ceil(len(ranked) * ratio))
        high, rest = ranked.iloc[:k], ranked.iloc[k:]
        if len(rest) == 0:
            return {"status": "unavailable", "reason": "비교할 나머지 그룹이 없습니다."}
        cols = self.sensors if columns is None else self.columns(columns)
        rows = []
        for c in cols:
            a, b = high[c].dropna(), rest[c].dropna()
            pooled = math.sqrt((a.var(ddof=0) + b.var(ddof=0)) / 2) if len(a) and len(b) else np.nan
            effect = (a.mean() - b.mean()) / pooled if pd.notna(pooled) and pooled > 0 else np.nan
            rows.append({"sensor": c, "high_mean": a.mean(), "rest_mean": b.mean(), "standardized_difference": effect,
                         "high_valid_count": len(a), "rest_valid_count": len(b)})
        rows.sort(key=lambda r: abs(r["standardized_difference"]) if pd.notna(r["standardized_difference"]) else -1, reverse=True)
        rows = rows[:15]
        return {"review_ratio": ratio, "high_count": len(high), "rest_count": len(rest), "rows": rows,
                "note": "평균 차이이며 인과관계나 SHAP 기여도가 아닙니다.",
                "charts": [chart("고위험군과 나머지의 표준화 평균 차이", [r["sensor"] for r in rows], [r["standardized_difference"] for r in rows])]}

    def correlate(self, columns=None, target="risk_score", method="pearson"):
        self.columns([target])
        if method not in ["pearson", "spearman"]:
            raise DataError("method는 pearson 또는 spearman이어야 합니다.")
        cols = self.sensors if columns is None else self.columns(columns)
        rows = []
        for c in cols:
            if c == target: continue
            pair = self.frame[[c, target]].dropna()
            coefficient = pair[c].corr(pair[target], method=method) if len(pair) >= 3 and pair[c].nunique() > 1 and pair[target].nunique() > 1 else np.nan
            rows.append({"column": c, "target": target, "method": method, "correlation": coefficient, "valid_count": len(pair)})
        rows.sort(key=lambda r: abs(r["correlation"]) if pd.notna(r["correlation"]) else -1, reverse=True)
        rows = rows[:15]
        return {"rows": rows, "note": "상관관계는 고장 원인을 확정하지 않습니다.",
                "charts": [chart("위험 점수와의 상관계수" if target == "risk_score" else f"{target}와의 상관계수", [r["column"] for r in rows], [r["correlation"] for r in rows])]}

    def time_summary(self, frequency="month"):
        periods = {"day": "D", "week": "W", "month": "M"}
        if frequency not in periods:
            raise DataError("frequency는 day, week, month 중 하나여야 합니다.")
        if "timestamp" not in self.frame or self.frame.timestamp.notna().sum() == 0:
            return {"status": "unavailable", "reason": "측정 시각 timestamp가 없습니다."}
        frame = self.frame.copy()
        times = pd.to_datetime(frame.timestamp, format="mixed", errors="coerce", utc=True)
        frame = frame.loc[times.notna()].copy()
        frame["period"] = times.loc[times.notna()].dt.tz_localize(None).dt.to_period(periods[frequency]).astype(str)
        rows = []
        for period, group in frame.groupby("period", sort=True):
            label = group.get("actual_label", pd.Series(np.nan, index=group.index))
            known = int(label.notna().sum())
            rows.append({"period": period, "count": len(group), "mean_risk_score": group.risk_score.mean(),
                         "known_label_count": known, "confirmed_failures": int((label == 1).sum()) if known else None,
                         "confirmed_failure_rate": float((label == 1).sum()/known) if known else None})
        return {"rows": rows[:100], "total_periods": len(rows), "excluded_missing_timestamps": len(self.frame)-len(frame),
                "charts": [chart("기간별 실제 표본 수", [r["period"] for r in rows[:100]], [r["count"] for r in rows[:100]]),
                           chart("기간별 평균 위험 점수", [r["period"] for r in rows[:100]], [r["mean_risk_score"] for r in rows[:100]], "line")]}

    def compare_reference(self, columns=None):
        if self.metadata['model_version'] != self.model.version:
            raise DataError("현재 모델과 데이터셋의 버전이 달라 학습 참고군을 비교할 수 없습니다.")
        reference = self.model.reference()
        cols = list(reference.columns) if columns is None else self.columns(columns)
        if any(c not in reference for c in cols):
            raise DataError("모델 학습 정상군에 없는 센서는 비교할 수 없습니다.")
        rows = []
        for c in cols:
            a, b = self.frame[c].dropna(), reference[c].dropna()
            std = b.std(ddof=0)
            shift = (a.mean()-b.mean())/std if len(a) and len(b) and std > 0 else np.nan
            rows.append({"sensor": c, "input_mean": a.mean(), "reference_mean": b.mean(), "reference_std": std,
                         "shift_in_reference_std": shift, "input_valid_count": len(a), "reference_valid_count": len(b)})
        rows.sort(key=lambda r: abs(r["shift_in_reference_std"]) if pd.notna(r["shift_in_reference_std"]) else -1, reverse=True)
        return {"reference": "학습 기준 정상군 표본 (Baseline Reference)", "reference_rows": len(reference), "rows": rows[:15],
                "note": "고정 참고 분포 대비 평균 이동입니다. 자동 정비·인터락을 발령하지 않습니다."}

    def evaluate_predictions(self, review_ratio=.2):
        ratio = ratio_value(review_ratio)
        label = self.frame.get("actual_label", pd.Series(np.nan, index=self.frame.index))
        if label.isna().any():
            return {"status": "unavailable", "reason": "전체 평가 표본의 정답 라벨이 필요합니다.", "known_label_count": int(label.notna().sum()), "total_count": len(label)}
        ranked = self.frame.sort_values(["risk_score", "row_id"], ascending=[False, True])
        k = int(math.ceil(len(ranked)*ratio))
        tp = int((ranked.iloc[:k].actual_label == 1).sum())
        fp = k-tp
        fn = int((ranked.iloc[k:].actual_label == 1).sum())
        tn = len(ranked)-k-fn
        base = (tp+fn)/len(ranked)
        return {"status": "available", "review_ratio": ratio, "total_count": len(ranked), "selected_count": k,
                "TP": tp, "FP": fp, "FN": fn, "TN": tn, "recall": tp/(tp+fn) if tp+fn else None,
                "precision": tp/k, "lift": (tp/k)/base if base else None,
                "note": "상위 검토 비율을 예측 양성으로 정의한 배치 평가입니다. 모델의 0.5 분류 임계값 평가와 다릅니다."}

    def explain_sample(self, row_id):
        if isinstance(row_id, bool) or not isinstance(row_id, int):
            raise DataError("row_id는 정수여야 합니다.")
        return self.model.explain(self.frame, row_id, self.metadata["model_version"])

    def diagnose_sample(self, sample_id, review_ratio=None):
        from .diagnostics import sample_diagnosis
        return sample_diagnosis(self,sample_id,review_ratio)

    def sensor_drift(self, direction='both', limit=20):
        from .diagnostics import temporal_drift
        result=temporal_drift(self,direction,limit)
        result['charts']=[chart('시간 변화 종합 드리프트 지수',[r['sensor'] for r in result['rows']],
                                [r['drift_index'] for r in result['rows']])]
        result['charts'] += [chart(s['sensor']+' 월별 원본 평균',[r['period'] for r in s['rows']],
                                   [r['mean'] for r in s['rows']],'line') for s in result.get('time_series',[])]
        return result

    def global_shap(self, limit=15, max_samples=200):
        limit_value(limit)
        if isinstance(max_samples,bool) or not isinstance(max_samples,int) or not 1<=max_samples<=500:
            raise DataError('max_samples는 1~500 정수여야 합니다.')
        result=self.model.global_explain(self.frame,self.metadata['model_version'],limit,max_samples)
        result['charts']=[chart('평균 절대 SHAP 중요도',[r['feature'] for r in result['rows']],
                                [r['mean_abs_shap'] for r in result['rows']])]
        return result

    def report(self):
        names = ["profile_dataset", "compare_groups", "correlate", "time_summary", "compare_reference", "evaluate_predictions"]
        results = []
        for name in names:
            try:
                results.append(self.execute(name))
            except (DataError, FileNotFoundError, RuntimeError) as exc:
                results.append({"tool": name, "data": {"status": "unavailable", "reason": str(exc)}})
        questions = ["이 파일의 결측률과 데이터 품질을 요약해줘", "위험도 상위 20%와 나머지의 센서 특성을 비교해줘",
                     "위험 점수와 관련이 큰 센서와 유효 표본 수를 보여줘", "학습 기준 정상군과 분포가 다른 센서를 찾아줘"]
        if "timestamp" in self.frame: questions.append("실제 월별 표본 수와 평균 위험 점수 변화를 보여줘")
        if "actual_label" in self.frame and self.frame.actual_label.notna().all(): questions.append("이번 파일의 상위 20% 검토 성능과 놓친 불량을 계산해줘")
        sample=str(self.frame.sort_values(['risk_score','row_id'],ascending=[False,True]).iloc[0].sample_id)
        questions.append(f"표본 {sample}의 센서 편차와 SHAP, 점검 시 확인할 내용을 분석해줘")
        questions.append("전체 센서의 평균 절대 SHAP 중요도와 분석 표본 수를 보여줘")
        if "timestamp" in self.frame:questions.append("시간 흐름에 따라 상승 또는 하강하는 센서를 드리프트 지수로 찾아줘")
        return {"metadata": self.metadata, "results": results, "suggested_questions": questions}
