import json
import os
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.parser import compute_hash, compute_match, parse_resume

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="AI 简历解析与匹配服务",
    description="支持 PDF 简历上传、关键信息抽取与岗位需求匹配评分的后端服务。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resume_cache: Dict[str, Dict] = {}
match_cache: Dict[str, Dict] = {}

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    def homepage() -> HTMLResponse:
        index_path = FRONTEND_DIR / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="前端页面未找到")
        return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/api/upload/")
async def upload_resume(resume: UploadFile = File(...)) -> JSONResponse:
    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式简历上传。")
    content = await resume.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空。")

    resume_id = compute_hash(content)
    parsed = parse_resume(content)
    resume_cache[resume_id] = parsed

    return JSONResponse({
        "resume_id": resume_id,
        "parsed": parsed,
        "message": "简历解析完成，已缓存解析结果。",
    })


@app.post("/api/match/")
async def match_resume(
    job_description: Dict[str, str],
) -> JSONResponse:
    body = job_description
    job_text = body.get("job_description")
    resume_id = body.get("resume_id")
    resume_text = body.get("resume_text")

    if not job_text:
        raise HTTPException(status_code=400, detail="job_description 字段为必填。")

    parsed = None
    if resume_id:
        parsed = resume_cache.get(resume_id)
        if not parsed:
            raise HTTPException(status_code=404, detail="未找到指定 resume_id 的简历缓存。")
    elif resume_text:
        parsed = {
            "resume_id": "inline",
            "text": resume_text,
            "basic_info": {},
            "background": {},
            "career": {"skills": resume_text, "projects": resume_text},
            "keywords": [],
        }
    else:
        raise HTTPException(status_code=400, detail="请提供 resume_id 或 resume_text。")

    cache_key = f"{parsed.get('resume_id')}::{hash(job_text)}"
    if cache_key in match_cache:
        return JSONResponse({"result": match_cache[cache_key], "cached": True})

    result = compute_match(parsed, job_text)
    match_cache[cache_key] = result
    return JSONResponse({"result": result, "cached": False})


@app.get("/api/resume/{resume_id}/")
def get_resume(resume_id: str) -> JSONResponse:
    parsed = resume_cache.get(resume_id)
    if not parsed:
        raise HTTPException(status_code=404, detail="未找到指定 resume_id 的简历缓存。")
    return JSONResponse(parsed)


@app.get("/api/ping/")
def ping() -> Dict[str, str]:
    return {"status": "ok", "message": "服务正常运行"}
