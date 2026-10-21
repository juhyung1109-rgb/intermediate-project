import gzip
import io
import json
import os
import sqlite3
import uuid
from pathlib import Path

import pandas as pd

from .validation import clean_json


def dataset_key(owner, file_hash, version):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"semiguard:{owner}:{file_hash}:{version}"))


def csv_frame(text):
    return pd.read_csv(io.StringIO(text), dtype={"sample_id": "string"})


class SQLiteRepository:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, owner TEXT NOT NULL, metadata TEXT NOT NULL, raw TEXT NOT NULL, predictions TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, owner TEXT NOT NULL, dataset TEXT NOT NULL, messages TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def save(self, owner, metadata, raw, predictions):
        with self.connect() as db:
            db.execute("INSERT INTO datasets VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET metadata=excluded.metadata, predictions=excluded.predictions",
                       (metadata["dataset_id"], owner, json.dumps(clean_json(metadata), ensure_ascii=False), raw.to_csv(index=False), predictions.to_csv(index=False)))
        return self.get(owner, metadata["dataset_id"])

    def get(self, owner, dataset_id):
        with self.connect() as db:
            row = db.execute("SELECT metadata, raw, predictions FROM datasets WHERE id=?", (dataset_id,)).fetchone()
        if row is None:
            raise KeyError("데이터셋을 찾을 수 없습니다.")
        return json.loads(row[0]), csv_frame(row[1]), csv_frame(row[2])

    def list(self, owner=None):
        with self.connect() as db:
            rows = db.execute("SELECT metadata FROM datasets ORDER BY rowid DESC LIMIT 50").fetchall()
        return [json.loads(r[0]) for r in rows]

    def conversation(self, owner, dataset_id, conversation_id):
        with self.connect() as db:
            row = db.execute("SELECT messages FROM conversations WHERE id=? AND owner=? AND dataset=?", (conversation_id, owner, dataset_id)).fetchone()
        if row is None:
            raise KeyError("이 데이터셋의 대화를 찾을 수 없습니다.")
        return json.loads(row[0])

    def save_conversation(self, owner, dataset_id, conversation_id, messages):
        with self.connect() as db:
            db.execute("INSERT INTO conversations VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET messages=excluded.messages WHERE conversations.owner=excluded.owner AND conversations.dataset=excluded.dataset",
                       (conversation_id, owner, dataset_id, json.dumps(messages[-20:], ensure_ascii=False)))

    def clear(self, owner=None):
        with self.connect() as db:
            if owner:
                db.execute("DELETE FROM datasets WHERE owner=?", (owner,))
                db.execute("DELETE FROM conversations WHERE owner=?", (owner,))
            else:
                db.execute("DELETE FROM datasets")
                db.execute("DELETE FROM conversations")



class GCSRepository:
    def __init__(self, bucket):
        from google.cloud import storage
        self.bucket = storage.Client().bucket(bucket)

    def _blob(self, owner, kind, key):
        uuid.UUID(key)
        return self.bucket.blob(f"analysis/{owner}/{kind}/{key}.json.gz")

    def _read(self, blob):
        from google.api_core.exceptions import NotFound
        try:
            return json.loads(gzip.decompress(blob.download_as_bytes()))
        except NotFound as exc:
            raise KeyError("데이터셋 또는 대화를 찾을 수 없습니다.") from exc

    def save(self, owner, metadata, raw, predictions):
        from google.api_core.exceptions import PreconditionFailed
        blob = self._blob(owner, "datasets", metadata["dataset_id"])
        payload = {"metadata": metadata, "raw": raw.to_csv(index=False), "predictions": predictions.to_csv(index=False)}
        try:
            blob.upload_from_string(gzip.compress(json.dumps(clean_json(payload), ensure_ascii=False).encode()), content_type="application/gzip", if_generation_match=0)
        except PreconditionFailed:
            pass
        return self.get(owner, metadata["dataset_id"])

    def get(self, owner, dataset_id):
        payload = self._read(self._blob(owner, "datasets", dataset_id))
        return payload["metadata"], csv_frame(payload["raw"]), csv_frame(payload["predictions"])

    def list(self, owner):
        blobs = self.bucket.list_blobs(prefix=f"analysis/{owner}/datasets/", max_results=50)
        return sorted([self._read(b)["metadata"] for b in blobs], key=lambda m: m["created_at"], reverse=True)

    def conversation(self, owner, dataset_id, conversation_id):
        payload = self._read(self._blob(owner, "conversations", conversation_id))
        if payload["dataset_id"] != dataset_id:
            raise KeyError("이 데이터셋의 대화를 찾을 수 없습니다.")
        return payload["messages"]

    def save_conversation(self, owner, dataset_id, conversation_id, messages):
        blob = self._blob(owner, "conversations", conversation_id)
        blob.upload_from_string(gzip.compress(json.dumps({"dataset_id": dataset_id, "messages": messages[-20:]}, ensure_ascii=False).encode()), content_type="application/gzip")


def create_repository(root):
    mode = os.getenv("DATASET_STORAGE", "sqlite")
    if mode == "gcs":
        bucket = os.environ.get("DATASET_BUCKET")
        if not bucket:
            raise RuntimeError("DATASET_STORAGE=gcs 환경에서는 DATASET_BUCKET이 필요합니다.")
        return GCSRepository(bucket)
    # Default SQLite repository (works locally and in Cloud Run instances)
    db_path = os.getenv("DATASET_DB", str(Path(root) / "runtime/analysis.sqlite3"))
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return SQLiteRepository(db_path)
