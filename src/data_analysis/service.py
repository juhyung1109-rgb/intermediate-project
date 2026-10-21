import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .repository import dataset_key
from .tools import AnalysisTools
from .validation import parse_csv, clean_json


class DatasetService:
    def __init__(self, repository, model_service):
        self.repository = repository
        self.model = model_service

    def ingest(self, owner, filename, contents, source_type="upload"):
        raw = parse_csv(contents)
        predictions = self.model.predict(raw)
        digest = hashlib.sha256(contents).hexdigest()
        metadata = {"dataset_id": dataset_key(owner, digest, self.model.version), "filename": Path(filename).name,
                    "file_sha256": digest, "model_version": self.model.version, "schema_version": "3.0",
                    "created_at": datetime.now(timezone.utc).isoformat(), "row_count": len(raw),
                    "sensor_count": len([c for c in raw if c.startswith("feature_")]),
                    "source_type": source_type, "status": "completed"}
        # Store raw and predictions together. No partially published dataset exists.
        stored = self.repository.save(owner, metadata, raw, predictions)
        tools = AnalysisTools(*stored, self.model)
        frame = tools.frame.sort_values("risk_rank")
        rows = clean_json(frame[[c for c in ["row_id", "sample_id", "timestamp", "actual_label", "risk_score", "risk_rank", "is_top20_review", "abnormal_sensor_count"] if c in frame]].to_dict("records"))
        return {"dataset_id": stored[0]["dataset_id"], "metadata": stored[0], "total_count": len(frame),
                "top20_count": int(frame.is_top20_review.sum()), "max_risk": float(frame.risk_score.max()),
                "mean_risk": float(frame.risk_score.mean()), "results": rows[:25], "full_results": rows,
                "report": tools.report()}

    def tools(self, owner, dataset_id):
        return AnalysisTools(*self.repository.get(owner, dataset_id), self.model)
