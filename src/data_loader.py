import os
import pandas as pd
import numpy as np

def prepare_secom_dataset(base_dir="."):
    """
    SECOM 원본 데이터(secom.data, secom_labels.data)를 정제하여
    data/processed/secom_features.csv 및 secom_labels.csv로 저장하는 파이프라인 함수.
    
    주요 정제 내용:
    1. 590개 센서 열 검증 및 'feature_1' ~ 'feature_590' 컬럼명 부여
    2. sample_id (0 ~ 1566) 인덱스 부여
    3. 라벨 변환 (-1 -> 0 정상: 1,463건, 1 -> 1 불량: 104건)
    4. 타임스탬프 파싱 (%d/%m/%Y %H:%M:%S)
    """
    # 원본 파일 경로 탐색 (data/raw 우선, 없으면 secom_extracted)
    raw_dir = os.path.join(base_dir, "data", "raw")
    if not os.path.exists(os.path.join(raw_dir, "secom.data")):
        raw_dir = os.path.join(base_dir, "secom_extracted")
        
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    data_path = os.path.join(raw_dir, "secom.data")
    labels_path = os.path.join(raw_dir, "secom_labels.data")
    
    print("[1/3] secom.data 로드 및 590열 정합성 검증...")
    # 공백 구분자 파싱 (결측값은 NaN)
    df_features = pd.read_csv(data_path, sep=r"\s+", header=None)
    
    # 590열 및 1567행 검증
    assert df_features.shape == (1567, 590), f"형태 불일치: 기대값 (1567, 590), 실제값 {df_features.shape}"
    df_features.columns = [f"feature_{i}" for i in range(1, 591)]
    df_features["sample_id"] = np.arange(len(df_features))
    
    print("[2/3] secom_labels.data 로드 및 라벨/타임스탬프 변환...")
    # 라벨 포맷: -1 "19/07/2008 11:55:00"
    labels = []
    timestamps = []
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('"')
            label_val = int(parts[0].strip())
            ts_val = parts[1].strip() if len(parts) > 1 else ""
            labels.append(label_val)
            timestamps.append(ts_val)
            
    df_labels = pd.DataFrame({
        "sample_id": np.arange(len(labels)),
        "raw_label": labels,
        # -1은 0(정상), 1은 1(불량)으로 변환
        "label": [1 if l == 1 else 0 for l in labels],
        "timestamp": pd.to_datetime(timestamps, format="%d/%m/%Y %H:%M:%S")
    })
    
    # 검증: 정상 1463, 불량 104
    label_counts = df_labels["label"].value_counts()
    assert label_counts[0] == 1463 and label_counts[1] == 104, (
        f"라벨 분포 불일치: 정상 {label_counts.get(0, 0)}건, 불량 {label_counts.get(1, 0)}건"
    )
    
    print("[3/3] 정제 CSV 파일 저장...")
    features_out = os.path.join(processed_dir, "secom_features.csv")
    labels_out = os.path.join(processed_dir, "secom_labels.csv")
    
    df_features.to_csv(features_out, index=False)
    df_labels.to_csv(labels_out, index=False)
    print(f"정제 데이터 저장 완료:\n  - features: {features_out}\n  - labels: {labels_out}")
    
    return df_features, df_labels

def load_processed_data(base_dir="."):
    """
    정제된 CSV 데이터를 로드하는 편의 함수.
    파일이 없을 경우 prepare_secom_dataset()을 자동 실행합니다.
    """
    features_out = os.path.join(base_dir, "data", "processed", "secom_features.csv")
    labels_out = os.path.join(base_dir, "data", "processed", "secom_labels.csv")
    
    if not (os.path.exists(features_out) and os.path.exists(labels_out)):
        return prepare_secom_dataset(base_dir)
        
    df_features = pd.read_csv(features_out)
    df_labels = pd.read_csv(labels_out)
    df_labels["timestamp"] = pd.to_datetime(df_labels["timestamp"])
    return df_features, df_labels

if __name__ == "__main__":
    prepare_secom_dataset()
