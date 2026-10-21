import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
import pandas as pd
import joblib

def build_cumulative_data():
    prep_path = r"artifacts\preprocessor.joblib"
    model_path = r"artifacts\baseline_model.joblib"
    
    prep = joblib.load(prep_path)
    model = joblib.load(model_path)
    valid_features = prep["valid_features"]
    scaler = prep.get("scaler")
    imputer = prep.get("imputer")

    print(f"Loaded model and preprocessor with {len(valid_features)} features.")

    # 1. Load existing 814 unified data to preserve exact baseline scores
    unified_js_path = r"web\data_unified814.js"
    with open(unified_js_path, "r", encoding="utf-8") as f:
        js_text = f.read()
    json_str = js_text.split("window.SEMI_UNIFIED_DATA = ", 1)[1].rsplit(";", 1)[0].strip()
    data_814 = json.loads(json_str)

    wafers_814 = data_814["wafers"]
    details_814 = data_814["wafer_details"]
    print(f"Loaded existing 814 wafers with {len(details_814)} details.")

    # 2. Score the 3 new simulation batches using the trained model
    batches = [
        ("sim_200", r"simulation\sim_batch_200_200904_200905.csv", "2009.04~05 (200매)"),
        ("sim_300", r"simulation\sim_batch_300_200906_200908.csv", "2009.06~08 (300매)"),
        ("sim_400", r"simulation\sim_batch_400_200909_200912.csv", "2009.09~12 (400매)")
    ]

    new_wafers = []
    new_details = {}

    for batch_key, csv_path, batch_name in batches:
        df = pd.read_csv(csv_path)
        print(f"Scoring {batch_name}: {len(df)} rows...")

        # Feature matrix
        X_df = df.reindex(columns=valid_features)
        
        # Impute and scale if preprocessor has them, or use df directly
        if imputer:
            X_imp = imputer.transform(X_df)
        else:
            X_imp = X_df.fillna(X_df.median()).values
            
        if scaler:
            X_scaled = scaler.transform(X_imp)
        else:
            X_scaled = X_imp

        # Model inference (predict_proba)
        probs = model.predict_proba(X_scaled)[:, 1]

        # Calculate mean & std for top abnormal sensors
        means = df[valid_features].mean()
        stds = df[valid_features].std().replace(0, 0.01).fillna(0.01)

        for i, row in df.iterrows():
            wid = str(int(row["sample_id"]))
            prob = float(probs[i])
            actual = int(row["actual_label"])
            ts = str(row["timestamp"])
            month = ts[:7]

            w_obj = {
                "sample_id": wid,
                "timestamp": ts,
                "month": month,
                "year": ts[:4],
                "actual_label": actual,
                "risk_score": prob,
                "source_lot": batch_key,
                "risk_score_pct": f"{(prob * 100):.2f}%"
            }
            new_wafers.append(w_obj)

            # Generate wafer detail
            # Compute z-scores across valid features
            row_feats = row.reindex(valid_features).astype(float)
            z_scores = (row_feats - means) / stds
            top_abnormal = z_scores.abs().sort_values(ascending=False).head(5)

            top_sensors = []
            for s_col in top_abnormal.index:
                val = float(row[s_col])
                z = float(z_scores[s_col])
                name_map = {
                    "feature_29": "feature_29 (CVD 챔버 배압 센서)",
                    "feature_60": "feature_60 (Dry Etch 하부 전극 전압)",
                    "feature_80": "feature_80 (Dry Etch 가스 질량유량)",
                    "feature_104": "feature_104 (Dry Etch RF 바이어스)",
                    "feature_170": "feature_170 (RF Matcher 정합기 인덕턴스)",
                    "feature_210": "feature_210 (CVD 챔버 칠러 압력)",
                    "feature_489": "feature_489 (CVD 서셉터 열전대 센서)",
                    "feature_512": "feature_512 (Dry Etch 전원 서지 전압)"
                }
                desc_name = name_map.get(s_col, s_col)
                top_sensors.append({
                    "sensor_id": s_col,
                    "name": desc_name,
                    "value": round(val, 4),
                    "z_score": round(z, 2),
                    "status": "🚨 관리선 초과 경보" if abs(z) >= 2.0 else "⚠️ 주의 관리선",
                    "normal_median": round(float(means[s_col]), 4)
                })

            summary = f"[{batch_name} 웨이퍼 #{wid}] LightGBM 추론 위험도 {(prob * 100):.2f}%. {'실제 불량(Defect) 적발 웨이퍼.' if actual == 1 else '정상 양품 웨이퍼.'}"

            new_details[wid] = {
                "id": wid,
                "sample_id": wid,
                "timestamp": ts,
                "month": month,
                "year": ts[:4],
                "actual_label": actual,
                "risk_score": prob,
                "top_abnormal_sensors": top_sensors,
                "summary": summary
            }

    # 3. Combine all 1,714 wafers
    # For wafers_814, add 'year' field
    for w in wafers_814:
        w["year"] = w["timestamp"][:4]

    all_wafers = wafers_814 + new_wafers
    # Sort all wafers by risk_score descending to assign global ranks
    all_wafers.sort(key=lambda x: x["risk_score"], reverse=True)

    for rank, w in enumerate(all_wafers, 1):
        w["global_rank"] = rank
        wid = str(w["sample_id"])
        if wid in details_814:
            details_814[wid]["global_rank"] = rank
            details_814[wid]["year"] = w["year"]
        if wid in new_details:
            new_details[wid]["global_rank"] = rank
            new_details[wid]["risk_rank"] = rank

    all_details = {**details_814, **new_details}

    # 4. Build Pre-calculated Cumulative Stages
    # Stage 1: 814 wafers
    # Stage 2: 1,014 wafers (+200)
    # Stage 3: 1,314 wafers (+300)
    # Stage 4: 1,714 wafers (+400)
    stages = {}
    stage_cutoffs = [
        ("stage_814", 814, "814매 전수 누적 (2008.07 ~ 2009.03)"),
        ("stage_1014", 1014, "1,014매 누적 (+200매: 2009.04 ~ 05 추가)"),
        ("stage_1314", 1314, "1,314매 누적 (+300매: 2009.06 ~ 08 추가)"),
        ("stage_1714", 1714, "1,714매 전사 종합 누적 (+400매: 2009.09 ~ 12 추가)")
    ]

    for stage_key, count, name in stage_cutoffs:
        subset = all_wafers[:count] if count == 1714 else [w for w in all_wafers if int(w["sample_id"]) <= (1565 if count == 814 and int(w["sample_id"]) < 2000 else (2500 if count == 814 else (2700 if count == 1014 else 3000)))]
        # Sort subset by risk_score descending to calculate local rank and top 20%
        subset_sorted = sorted(subset, key=lambda x: x["risk_score"], reverse=True)
        top20_cut = int(np.ceil(len(subset_sorted) * 0.20))
        
        tp = sum(1 for i, w in enumerate(subset_sorted) if i < top20_cut and w["actual_label"] == 1)
        fp = sum(1 for i, w in enumerate(subset_sorted) if i < top20_cut and w["actual_label"] == 0)
        fn = sum(1 for i, w in enumerate(subset_sorted) if i >= top20_cut and w["actual_label"] == 1)
        tn = sum(1 for i, w in enumerate(subset_sorted) if i >= top20_cut and w["actual_label"] == 0)
        fails = tp + fn
        total = len(subset_sorted)
        recall = round((tp / fails * 100), 2) if fails > 0 else 100.0
        prec = round((tp / (tp + fp) * 100), 2) if (tp + fp) > 0 else 0.0
        defect_rate = round((fails / total * 100), 2)
        lift = round(prec / defect_rate, 2) if defect_rate > 0 else 1.0

        stages[stage_key] = {
            "key": stage_key,
            "name": name,
            "total_count": total,
            "total_defects": fails,
            "defect_rate": defect_rate,
            "top20_cutoff": top20_cut,
            "confusion_matrix": {
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "TN": tn,
                "recall": recall,
                "precision": prec,
                "accuracy": round(((tp + tn) / total * 100), 2),
                "lift": lift
            }
        }
        print(f"[{stage_key}] Total: {total}, Defects: {fails} ({defect_rate}%), Top20: {top20_cut}, TP: {tp}, FP: {fp}, FN: {fn}, TN: {tn}, Recall: {recall}%, Lift: {lift}x")

    # 5. Build Monthly Statistics for ALL 18 months (2008-07 to 2009-12)
    monthly_stats = {}
    months = sorted(list(set(w["month"] for w in all_wafers)))
    for m in months:
        m_wafers = [w for w in all_wafers if w["month"] == m]
        m_sorted = sorted(m_wafers, key=lambda x: x["risk_score"], reverse=True)
        m_total = len(m_sorted)
        m_cut = int(np.ceil(m_total * 0.20))
        m_tp = sum(1 for i, w in enumerate(m_sorted) if i < m_cut and w["actual_label"] == 1)
        m_fails = sum(1 for w in m_sorted if w["actual_label"] == 1)
        m_recall = round((m_tp / m_fails * 100), 1) if m_fails > 0 else 100.0
        
        monthly_stats[m] = {
            "month": m,
            "total": m_total,
            "fails": m_fails,
            "defect_rate": round(m_fails / m_total * 100, 2),
            "top20_cut": m_cut,
            "tp": m_tp,
            "recall": m_recall,
            "wafers": [w["sample_id"] for w in m_sorted[:8]]
        }

    # 6. Build Yearly Statistics (2008 vs 2009)
    yearly_stats = {}
    for y in ["2008", "2009"]:
        y_wafers = [w for w in all_wafers if w["year"] == y]
        y_sorted = sorted(y_wafers, key=lambda x: x["risk_score"], reverse=True)
        y_total = len(y_sorted)
        y_cut = int(np.ceil(y_total * 0.20))
        y_tp = sum(1 for i, w in enumerate(y_sorted) if i < y_cut and w["actual_label"] == 1)
        y_fp = sum(1 for i, w in enumerate(y_sorted) if i < y_cut and w["actual_label"] == 0)
        y_fn = sum(1 for i, w in enumerate(y_sorted) if i >= y_cut and w["actual_label"] == 1)
        y_tn = sum(1 for i, w in enumerate(y_sorted) if i >= y_cut and w["actual_label"] == 0)
        y_fails = y_tp + y_fn
        y_recall = round((y_tp / y_fails * 100), 2) if y_fails > 0 else 100.0
        y_prec = round((y_tp / (y_tp + y_fp) * 100), 2) if (y_tp + y_fp) > 0 else 0.0
        y_rate = round((y_fails / y_total * 100), 2)
        y_lift = round(y_prec / y_rate, 2) if y_rate > 0 else 1.0

        yearly_stats[y] = {
            "year": y,
            "total_count": y_total,
            "total_defects": y_fails,
            "defect_rate": y_rate,
            "top20_cutoff": y_cut,
            "confusion_matrix": {
                "TP": y_tp,
                "FP": y_fp,
                "FN": y_fn,
                "TN": y_tn,
                "recall": y_recall,
                "precision": y_prec,
                "accuracy": round(((y_tp + y_tn) / y_total * 100), 2),
                "lift": y_lift
            }
        }

    # Export to web/data_cumulative_all.js
    output_js = r"web\data_cumulative_all.js"
    js_content = f"""// SEMI-GUARD Universal Continuous Production Dataset (1,714 Wafers, 2008.07 ~ 2009.12)
// Supports All-Time Cumulative, Yearly (2008/2009), and 18 Monthly Drill-downs
window.SEMI_CUMULATIVE_DATA = {{
  "total_count": {len(all_wafers)},
  "total_defects": {sum(1 for w in all_wafers if w["actual_label"] == 1)},
  "defect_rate": {round(sum(1 for w in all_wafers if w["actual_label"] == 1) / len(all_wafers) * 100, 2)},
  "top20_cutoff": {int(np.ceil(len(all_wafers) * 0.20))},
  "stages": {json.dumps(stages, indent=2, ensure_ascii=False)},
  "yearly_stats": {json.dumps(yearly_stats, indent=2, ensure_ascii=False)},
  "monthly_stats": {json.dumps(monthly_stats, indent=2, ensure_ascii=False)},
  "wafers": {json.dumps(all_wafers, indent=2, ensure_ascii=False)},
  "wafer_details": {json.dumps(all_details, indent=2, ensure_ascii=False)}
}};
"""
    with open(output_js, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"Exported {output_js} ({len(all_wafers)} total wafers, {len(all_details)} details).")

if __name__ == "__main__":
    build_cumulative_data()
