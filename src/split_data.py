import os
import pandas as pd
from sklearn.model_selection import train_test_split

def split_and_save_indices(base_dir=".", test_size=0.2, seed=42):
    """
    라벨 데이터를 기반으로 Train(80%, 1,253건)과 Test(20%, 314건)를
    불량 비율(6.64%)을 유지하며 층화 분리(Stratified Split)하고
    artifacts 폴더에 인덱스를 저장하여 누수를 영구 방지합니다.
    """
    labels_path = os.path.join(base_dir, "data", "processed", "secom_labels.csv")
    artifacts_dir = os.path.join(base_dir, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    
    if not os.path.exists(labels_path):
        from src.data_loader import prepare_secom_dataset
        prepare_secom_dataset(base_dir)
        
    df_labels = pd.read_csv(labels_path)
    
    train_df, test_df = train_test_split(
        df_labels,
        test_size=test_size,
        stratify=df_labels["label"],
        random_state=seed
    )
    
    train_indices = train_df[["sample_id", "label"]].sort_values("sample_id").reset_index(drop=True)
    test_indices = test_df[["sample_id", "label"]].sort_values("sample_id").reset_index(drop=True)
    
    train_out = os.path.join(artifacts_dir, "train_indices.csv")
    test_out = os.path.join(artifacts_dir, "test_indices.csv")
    
    train_indices.to_csv(train_out, index=False)
    test_indices.to_csv(test_out, index=False)
    
    n_train_fail = (train_indices['label'] == 1).sum()
    n_test_fail = (test_indices['label'] == 1).sum()
    train_fail_rate = (n_train_fail / len(train_indices)) * 100
    test_fail_rate = (n_test_fail / len(test_indices)) * 100
    
    print(f"층화 분리 완료:")
    print(f"  - Train: {len(train_indices):,}건 (불량: {n_train_fail}건, {train_fail_rate:.2f}%) -> {train_out}")
    print(f"  - Test:  {len(test_indices):,}건 (불량: {n_test_fail}건, {test_fail_rate:.2f}%) -> {test_out}")
    
    return train_indices, test_indices

def load_split_indices(base_dir="."):
    """저장된 Train / Test 인덱스를 불러옵니다."""
    train_out = os.path.join(base_dir, "artifacts", "train_indices.csv")
    test_out = os.path.join(base_dir, "artifacts", "test_indices.csv")
    
    if not (os.path.exists(train_out) and os.path.exists(test_out)):
        return split_and_save_indices(base_dir)
        
    return pd.read_csv(train_out), pd.read_csv(test_out)

if __name__ == "__main__":
    split_and_save_indices()
