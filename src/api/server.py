"""FastAPI server exposing the LocalMind agent."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import json
from pathlib import Path
from src.agent import core, memory

app = FastAPI(title="LocalMind", version="0.1.0")

# In-memory session store (keyed by session_id)
_sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.on_event("startup")
async def startup():
    await memory.init_memory()


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = _sessions.get(req.session_id, [])
    history.append({"role": "user", "content": req.message})
    reply, updated = await core.chat(history)
    _sessions[req.session_id] = updated
    return ChatResponse(reply=reply, session_id=req.session_id)


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    return {"messages": _sessions.get(session_id, [])}


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"status": "cleared"}


@app.get("/health")
async def health():
    return {"status": "ok", "offline": True}


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent.parent / "ui" / "index.html"
    return HTMLResponse(html_path.read_text())
