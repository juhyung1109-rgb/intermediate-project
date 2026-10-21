import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib

def generate_batches():
    base_csv = r"simulation\secom_test_batch_200811_200903.csv"
    if not os.path.exists(base_csv):
        print("Base simulation CSV not found:", base_csv)
        return

    df_base = pd.read_csv(base_csv)
    feature_cols = [c for c in df_base.columns if c.startswith("feature_")]
    print(f"Loaded base CSV with {len(df_base)} rows and {len(feature_cols)} features.")

    # Calculate base statistics for numerical features
    means = df_base[feature_cols].mean()
    stds = df_base[feature_cols].std().replace(0, 0.01).fillna(0.01)

    np.random.seed(42)

    # 1. Batch 200: 2009-04-01 ~ 2009-05-31 (200 wafers: 2501 ~ 2700)
    # Scenario: 4월 정상(4.0%), 5월 CVD 온도 센서(feature_489) 및 RF 매처(feature_170) 미세 편차(5.0%)
    generate_single_batch(
        df_base=df_base,
        feature_cols=feature_cols,
        means=means,
        stds=stds,
        start_id=2501,
        count=200,
        start_date=datetime(2009, 4, 1, 8, 30, 0),
        end_date=datetime(2009, 5, 31, 20, 0, 0),
        defect_count=9, # 4.5% defect rate
        output_path=r"simulation\sim_batch_200_200904_200905.csv",
        drift_scenario="spring_rf_matcher"
    )

    # 2. Batch 300: 2009-06-01 ~ 2009-08-31 (300 wafers: 2701 ~ 3000)
    # Scenario: 6월 초기(4.0%), 7월 칠러 냉각수 저하(7.0%), 8월 하계 피크 스파이크(11.0% - feature_60, feature_104 마모)
    generate_single_batch(
        df_base=df_base,
        feature_cols=feature_cols,
        means=means,
        stds=stds,
        start_id=2701,
        count=300,
        start_date=datetime(2009, 6, 1, 8, 0, 0),
        end_date=datetime(2009, 8, 31, 22, 0, 0),
        defect_count=22, # 7.33% defect rate
        output_path=r"simulation\sim_batch_300_200906_200908.csv",
        drift_scenario="summer_peak_spike"
    )

    # 3. Batch 400: 2009-09-01 ~ 2009-12-31 (400 wafers: 3001 ~ 3400)
    # Scenario: 9월 PM 복구(3.0%), 10월 초고수율(2.0%), 11월 정상(3.0%), 12월 안정(4.0%)
    generate_single_batch(
        df_base=df_base,
        feature_cols=feature_cols,
        means=means,
        stds=stds,
        start_id=3001,
        count=400,
        start_date=datetime(2009, 9, 1, 8, 0, 0),
        end_date=datetime(2009, 12, 31, 21, 0, 0),
        defect_count=12, # 3.0% defect rate
        output_path=r"simulation\sim_batch_400_200909_200912.csv",
        drift_scenario="autumn_recovery_high_yield"
    )

def generate_single_batch(df_base, feature_cols, means, stds, start_id, count, start_date, end_date, defect_count, output_path, drift_scenario):
    # Sample rows from base to keep realistic structure
    sampled_indices = np.random.choice(len(df_base), size=count, replace=True)
    df_new = df_base.iloc[sampled_indices].copy().reset_index(drop=True)

    # Assign Sequential Sample IDs
    df_new["sample_id"] = [start_id + i for i in range(count)]

    # Assign Realistic Chronological Timestamps
    total_seconds = int((end_date - start_date).total_seconds())
    step = total_seconds // count
    timestamps = []
    current_time = start_date
    for i in range(count):
        jitter = np.random.randint(-1800, 1800) # +/- 30 min jitter
        t = current_time + timedelta(seconds=max(0, jitter))
        timestamps.append(t.strftime("%Y-%m-%d %H:%M:%S"))
        current_time += timedelta(seconds=step)
    df_new["timestamp"] = timestamps

    # Assign Actual Defect Labels
    # Distribute defect_count across wafers
    defect_indices = set()
    if drift_scenario == "summer_peak_spike":
        # Heavily concentrated in the last third (August)
        august_start = int(count * 0.66)
        candidates = list(range(august_start, count))
        defect_indices.update(np.random.choice(candidates, size=int(defect_count * 0.65), replace=False))
        remaining = defect_count - len(defect_indices)
        other_candidates = [i for i in range(august_start) if i not in defect_indices]
        defect_indices.update(np.random.choice(other_candidates, size=remaining, replace=False))
    elif drift_scenario == "spring_rf_matcher":
        # Concentrated in second half (May)
        may_start = int(count * 0.5)
        candidates = list(range(may_start, count))
        defect_indices.update(np.random.choice(candidates, size=int(defect_count * 0.6), replace=False))
        remaining = defect_count - len(defect_indices)
        other_candidates = [i for i in range(may_start) if i not in defect_indices]
        defect_indices.update(np.random.choice(other_candidates, size=remaining, replace=False))
    else: # autumn_recovery_high_yield
        # Evenly spread, very low defect rate
        defect_indices.update(np.random.choice(count, size=defect_count, replace=False))

    labels = [1 if i in defect_indices else 0 for i in range(count)]
    df_new["actual_label"] = labels

    # Apply Sensor Drift Scenarios
    for i in range(count):
        is_defect = (labels[i] == 1)
        if drift_scenario == "summer_peak_spike" and i >= int(count * 0.6):
            # August Peak: feature_60 drops (-1.8 sigma), feature_104 drops (-1.9 sigma)
            if "feature_60" in df_new.columns:
                df_new.loc[i, "feature_60"] = means["feature_60"] - 1.8 * stds["feature_60"] + np.random.normal(0, 0.1 * stds["feature_60"])
            if "feature_104" in df_new.columns:
                df_new.loc[i, "feature_104"] = means["feature_104"] - 1.9 * stds["feature_104"] + np.random.normal(0, 0.1 * stds["feature_104"])
            if is_defect:
                if "feature_512" in df_new.columns:
                    df_new.loc[i, "feature_512"] = means["feature_512"] + 2.4 * stds["feature_512"] # surge

        elif drift_scenario == "spring_rf_matcher" and i >= int(count * 0.5):
            # May: feature_170 rises (+1.6 sigma)
            if "feature_170" in df_new.columns:
                df_new.loc[i, "feature_170"] = means["feature_170"] + 1.6 * stds["feature_170"] + np.random.normal(0, 0.1 * stds["feature_170"])
            if is_defect and "feature_489" in df_new.columns:
                df_new.loc[i, "feature_489"] = 0.0 # thermocouple dropout

        elif drift_scenario == "autumn_recovery_high_yield":
            # PM completed: sensors returned to normal mean +/- 0.3 sigma
            if "feature_29" in df_new.columns:
                df_new.loc[i, "feature_29"] = means["feature_29"] + np.random.normal(0, 0.3 * stds["feature_29"])
            if "feature_60" in df_new.columns:
                df_new.loc[i, "feature_60"] = means["feature_60"] + np.random.normal(0, 0.3 * stds["feature_60"])

    # Ensure columns order: sample_id, timestamp, actual_label, feature_1 ...
    cols = ["sample_id", "timestamp", "actual_label"] + feature_cols
    df_new = df_new[cols]

    df_new.to_csv(output_path, index=False)
    print(f"Generated {output_path} ({len(df_new)} rows, {defect_count} defects, {drift_scenario})")

if __name__ == "__main__":
    generate_batches()
