"""SEMI-GUARD v3: fitted batch inference and dataset-scoped analysis tools."""
import hashlib
import io
import json
import os
import re
import secrets
from pathlib import Path
from uuid import UUID

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from src.data_analysis.agent import AnalysisAgent, AgentUnavailable, TOOL_DESCRIPTIONS
from src.data_analysis.inference import ModelService
from src.data_analysis.repository import create_repository
from src.data_analysis.service import DatasetService
from src.data_analysis.validation import DataError, clean_json
from server.user_sync import UserSyncRequest, sync_user_to_firestore
from server.dashboard_api import create_dashboard_router

BASE_DIR = Path(__file__).resolve().parents[1]
model_service = ModelService(BASE_DIR)
repository = create_repository(BASE_DIR)
service = DatasetService(repository, model_service)
agent = AnalysisAgent(service)
app = FastAPI(title="SEMI-GUARD CSV 분석 서비스", version="3.0.0")


@app.middleware("http")
async def dataset_session(request: Request, call_next):
    user_email = request.headers.get("X-User-Email", "").strip().lower()
    if user_email:
        request.state.owner = hashlib.sha256(user_email.encode()).hexdigest()
    else:
        token = request.cookies.get("semiguard_analysis_session", "")
        valid = bool(re.fullmatch(r"[0-9a-f]{64}", token))
        if not valid:
            token = secrets.token_hex(32)
        request.state.owner = hashlib.sha256(token.encode()).hexdigest()
    response = await call_next(request)
    if "semiguard_analysis_session" not in request.cookies:
        token = secrets.token_hex(32)
        response.set_cookie("semiguard_analysis_session", token, httponly=True, samesite="lax",
                            secure=request.url.scheme == "https", max_age=60*60*24*7)
    return response


@app.exception_handler(DataError)
async def data_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(KeyError)
async def missing_data(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc).strip("'")})


@app.exception_handler(RuntimeError)
async def unavailable(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    return {"status": "ready" if model_service.model is not None else "model_unavailable",
            "version": "3.0.0", "model_loaded": model_service.model is not None,
            "model_version": model_service.version, "features_count": len(model_service.features),
            "model_error": model_service.error, "agent_configured": agent.configured,
            "agent_provider": "gemini", "agent_model": agent.model,
            "storage": os.getenv("DATASET_STORAGE", "sqlite"), "tools": TOOL_DESCRIPTIONS}


# Retain the existing account-profile integration; dataset access uses server sessions.
app.post("/api/sync-user")(sync_user_to_firestore)


@app.post("/api/predict-batch")
async def predict_batch(request: Request, file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise DataError("CSV 파일을 선택해 주세요.")
    contents = await file.read(20*1024*1024 + 1)
    return await run_in_threadpool(service.ingest, request.state.owner, file.filename, contents)


def simulation_files():
    folder = BASE_DIR / "simulation"
    return {p.name: p for p in folder.glob("*.csv") if p.is_file() and not p.name.lower().startswith("secom_")}


@app.get("/api/simulation")
def list_simulation():
    return {"files": [{"filename": name, "bytes": path.stat().st_size, "source_type": "simulation"}
                       for name, path in sorted(simulation_files().items())]}


@app.post("/api/simulation/{filename}/analyze")
def analyze_simulation(filename: str, request: Request):
    path = simulation_files().get(filename)
    if path is None:
        raise KeyError("등록된 simulation CSV가 아닙니다.")
    return service.ingest(request.state.owner, filename, path.read_bytes(), "simulation")


@app.get("/api/datasets")
def list_datasets(request: Request):
    return {"datasets": repository.list(request.state.owner)}


@app.post("/api/datasets/reset")
def reset_datasets(request: Request, all: bool = True):
    if all:
        repository.clear()
    else:
        repository.clear(request.state.owner)
    return {"status": "ok", "message": "모든 업로드 데이터셋이 깨끗하게 초기화되었습니다."}


@app.get("/api/datasets/{dataset_id}")
def dataset_details(dataset_id: UUID, request: Request, offset: int = 0, limit: int = 50):
    if not 0 <= offset <= 10000 or not 1 <= limit <= 100:
        raise DataError("offset은 0~10000, limit은 1~100 범위여야 합니다.")
    tools = service.tools(request.state.owner, str(dataset_id))
    frame = tools.frame.sort_values("risk_rank")
    columns = [c for c in ["row_id", "sample_id", "timestamp", "actual_label", "risk_score", "risk_rank", "is_top20_review", "abnormal_sensor_count"] if c in frame]
    return clean_json({"metadata": tools.metadata, "columns": list(frame.columns), "total_count": len(frame),
                       "rows": frame[columns].iloc[offset:offset+limit].to_dict("records")})


@app.get("/api/datasets/{dataset_id}/report")
def dataset_report(dataset_id: UUID, request: Request):
    return service.tools(request.state.owner, str(dataset_id)).report()


class ToolRequest(BaseModel):
    arguments: dict = Field(default_factory=dict)


@app.post("/api/datasets/{dataset_id}/tools/{tool_name}")
def run_tool(dataset_id: UUID, tool_name: str, req: ToolRequest, request: Request):
    return service.tools(request.state.owner, str(dataset_id)).execute(tool_name, req.arguments)


@app.get("/api/datasets/{dataset_id}/export")
def export_dataset(dataset_id: UUID, request: Request):
    frame = service.tools(request.state.owner, str(dataset_id)).frame
    data = frame.sort_values("row_id").to_csv(index=False).encode("utf-8-sig")
    return StreamingResponse(io.BytesIO(data), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="analysis_{dataset_id}.csv"'})


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=3000)
    dataset_id: UUID
    conversation_id: UUID | None = None


@app.post("/api/chat")
def analyze_question(req: ChatRequest, request: Request):
    return agent.answer(request.state.owner, str(req.dataset_id), req.query,
                        str(req.conversation_id) if req.conversation_id else None)


@app.get("/api/evaluation")
def stored_evaluation():
    frame = pd.read_csv(BASE_DIR / "artifacts/test_predictions.csv")
    frame = frame.sort_values(["risk_score", "sample_id"], ascending=[False, True])
    k = int(__import__('math').ceil(len(frame)*.2))
    tp = int(frame.head(k).actual_label.eq(1).sum())
    fails = int(frame.actual_label.eq(1).sum())
    return clean_json({"source": "보관된 SECOM 시험 예측 (artifacts/test_predictions.csv)",
                       "train_count": len(pd.read_csv(BASE_DIR / "artifacts/train_indices.csv")),
                       "test_count": len(frame), "selected_count": k, "TP": tp, "FP": k-tp,
                       "FN": fails-tp, "TN": len(frame)-k-fails+tp, "recall": tp/fails if fails else None,
                       "rows": frame.head(20).to_dict("records"),
                       "note": "사용자 업로드 성능과 구분된 과거 시험 결과입니다. 모델 선정에 사용한 시험셋은 독립 재평가가 필요합니다."})


@app.get("/proposal")
def proposal():
    return FileResponse(BASE_DIR / "docs/반도체_공정_데이터분석_시각화_서비스_기획서.html")


@app.get("/proposal/v1.1")
def proposal_revision():
    return FileResponse(BASE_DIR / "docs/반도체_공정_데이터분석_시각화_서비스_기획안_v1.1.html")


@app.get("/api/download/{kind}")
def historical_download(kind: str):
    paths = {"csv": BASE_DIR / "artifacts/test_predictions.csv", "report": BASE_DIR / "artifacts/SECOM_공정_품질_종합_진단_보고서.md"}
    if kind not in paths or not paths[kind].exists():
        raise KeyError("다운로드 파일을 찾을 수 없습니다.")
    return FileResponse(paths[kind], filename=paths[kind].name)


def seed_default_dataset_if_empty():
    try:
        current = repository.list()
        if not current:
            target = BASE_DIR / "simulation/sim_batch_400_200909_200912.csv"
            if not target.exists():
                sims = sorted((BASE_DIR / "simulation").glob("*.csv"))
                if sims:
                    target = sims[0]
            if target.exists():
                service.ingest("fab_shared", target.name, target.read_bytes(), "simulation")
                print(f"[SEMI-GUARD] Pre-seeded default dataset: {target.name}")
    except Exception as e:
        print("[SEMI-GUARD] Pre-seed notice:", e)

seed_default_dataset_if_empty()

app.include_router(create_dashboard_router(service))
app.mount("/picture", StaticFiles(directory=BASE_DIR / "picture"), name="picture")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "docs/assets"), name="proposal-assets")
app.mount("/", StaticFiles(directory=BASE_DIR / "web", html=True), name="web")
