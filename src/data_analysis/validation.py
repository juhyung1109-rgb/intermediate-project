import csv
import io
import re

import numpy as np
import pandas as pd


class DataError(ValueError):
    pass


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def parse_csv(contents):
    if not contents or len(contents) > 20 * 1024 * 1024:
        raise DataError("CSV는 비어 있지 않은 20 MiB 이하 파일이어야 합니다.")
    try:
        text = contents.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text), strict=True)
        header = next(reader)
        if len(header) != len(set(header)):
            raise DataError("CSV에 중복된 컬럼명이 있습니다.")
        if any(not c or c != c.strip() for c in header):
            raise DataError("컬럼명에는 빈 이름이나 앞뒤 공백을 사용할 수 없습니다.")
        if any(row and len(row) != len(header) for row in reader):
            raise DataError("CSV 데이터 행의 열 수가 헤더와 다릅니다.")
        df = pd.read_csv(io.StringIO(text), dtype={"sample_id": "string"})
    except (UnicodeError, StopIteration, csv.Error, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DataError("UTF-8 형식의 유효한 CSV를 사용해 주세요.") from exc
    if len(df) == 0 or len(df) > 10000 or len(df.columns) > 650:
        raise DataError("CSV는 1~10,000행, 650열 이하를 지원합니다.")
    reserved = {"row_id", "risk_score", "risk_rank", "is_top20_review", "abnormal_sensor_count"}
    if reserved.intersection(df.columns):
        raise DataError("예측 출력 전용 컬럼은 업로드할 수 없습니다: " + ", ".join(sorted(reserved.intersection(df.columns))))
    sensors = [c for c in df if re.fullmatch(r"feature_\d+", c)]
    if any(c.startswith('feature_') and c not in sensors for c in df):
        raise DataError("센서 열은 feature_1 ~ feature_590 이름을 사용해 주세요.")
    if not sensors:
        raise DataError("feature_1 ~ feature_590 형식의 센서 열이 필요합니다.")
    if any(not 1 <= int(c[8:]) <= 590 for c in sensors):
        raise DataError("지원하는 센서 번호는 feature_1 ~ feature_590입니다.")
    for c in sensors:
        source = df[c]
        values = pd.to_numeric(source, errors="coerce")
        bad = source.notna() & values.isna()
        if bad.any():
            raise DataError(f"{c}의 CSV {int(np.flatnonzero(bad)[0])+2}행에 숫자가 아닌 값이 있습니다.")
        if np.isinf(values.to_numpy(dtype=float)).any():
            raise DataError(f"{c}에 무한대 값이 있습니다.")
        df[c] = values
    if "sample_id" not in df:
        df.insert(0, "sample_id", [f"sample_{i+1}" for i in range(len(df))])
    df["sample_id"] = df["sample_id"].astype("string").str.strip()
    if df.sample_id.isna().any() or (df.sample_id == "").any() or df.sample_id.duplicated().any():
        raise DataError("sample_id는 파일 안에서 비어 있지 않은 고유 값이어야 합니다.")
    if "label" in df and "actual_label" in df:
        raise DataError("label과 actual_label 중 한 컬럼만 제공해 주세요.")
    if "label" in df:
        df = df.rename(columns={"label": "actual_label"})
    if "actual_label" in df:
        label = pd.to_numeric(df.actual_label, errors="coerce")
        bad = (df.actual_label.notna() & label.isna()) | (label.notna() & ~label.isin([0, 1]))
        if bad.any():
            raise DataError("actual_label은 정상 0, 불량 1 또는 빈 값만 허용합니다.")
        df["actual_label"] = label
    if "timestamp" in df:
        times = pd.to_datetime(df.timestamp, errors="coerce", format="mixed")
        if (df.timestamp.notna() & times.isna()).any():
            raise DataError("timestamp에 해석할 수 없는 날짜가 있습니다. ISO 날짜 형식을 사용해 주세요.")
        df["timestamp"] = times.map(lambda v: v.isoformat() if pd.notna(v) else None)
    df = df.copy()
    df.insert(0, "row_id", np.arange(len(df), dtype=int))
    return df
