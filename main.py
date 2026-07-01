import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="IPC Hermes Bridge API",
    version="0.1.0",
    description="Bridge API để IPC Land gửi job sang Hermes/AI worker."
)

API_KEY = os.getenv("IPC_HERMES_API_KEY", "")

# MVP: lưu job trong RAM.
# Sau này nên chuyển sang database / IPC Land review queue.
JOBS: Dict[str, Dict[str, Any]] = {}


class ResearchKCNRequest(BaseModel):
    kcn_name: str = Field(..., examples=["VSIP Quảng Ngãi"])
    source_url: Optional[str] = Field(None, examples=["https://example.com/kcn-vsip-quang-ngai"])
    note: Optional[str] = Field(None, examples=["Ưu tiên lấy quy mô, chủ đầu tư, logistics, ngành phù hợp"])
    callback_url: Optional[str] = Field(None, examples=["https://ipcland.vn/api/hermes/callback"])
    requested_by: Optional[str] = Field("ipcland-admin", examples=["admin"])


class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str
    message: str


def verify_auth(authorization: Optional[str]):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server missing IPC_HERMES_API_KEY")

    expected = f"Bearer {API_KEY}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


async def fake_research_kcn(job_id: str, payload: ResearchKCNRequest):
    """
    MVP demo: giả lập research.
    Sau này thay bằng logic gọi Hermes/OpenRouter/Web research thật.
    """
    JOBS[job_id]["status"] = "running"
    JOBS[job_id]["updated_at"] = now_iso()

    await asyncio.sleep(3)

    result = {
        "type": "kcn_research",
        "kcn_name": payload.kcn_name,
        "source_url": payload.source_url,
        "summary": f"Bản nháp dữ liệu cho {payload.kcn_name}. Cần người quản trị IPC Land kiểm tra trước khi lưu DB.",
        "data": {
            "name": payload.kcn_name,
            "province": None,
            "scale_ha": None,
            "developer": None,
            "land_lease_price": None,
            "available_area": None,
            "infrastructure": {
                "power": None,
                "water": None,
                "wastewater_treatment": None
            },
            "logistics": {
                "nearest_port": None,
                "nearest_airport": None,
                "highway_connection": None
            },
            "suitable_industries": []
        },
        "missing_fields": [
            "province",
            "scale_ha",
            "developer",
            "land_lease_price",
            "available_area",
            "nearest_port",
            "nearest_airport"
        ],
        "confidence_score": 0.30,
        "sources": []
    }

    JOBS[job_id]["status"] = "completed"
    JOBS[job_id]["result"] = result
    JOBS[job_id]["updated_at"] = now_iso()

    if payload.callback_url:
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                await client.post(
                    payload.callback_url,
                    json={
                        "job_id": job_id,
                        "status": "completed",
                        "result": result
                    },
                    headers={
                        "X-IPC-Hermes-Job": job_id
                    }
                )
                JOBS[job_id]["callback_status"] = "sent"
            except Exception as e:
                JOBS[job_id]["callback_status"] = "failed"
                JOBS[job_id]["callback_error"] = str(e)


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "ipc-hermes-bridge",
        "time": now_iso()
    }


@app.post("/api/v1/research/kcn", response_model=JobAcceptedResponse)
async def create_research_kcn_job(
    payload: ResearchKCNRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    JOBS[job_id] = {
        "job_id": job_id,
        "type": "research_kcn",
        "status": "queued",
        "request": payload.model_dump(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "result": None
    }

    background_tasks.add_task(fake_research_kcn, job_id, payload)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Research KCN job accepted"
    }


@app.get("/api/v1/jobs/{job_id}")
def get_job(
    job_id: str,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)

    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
