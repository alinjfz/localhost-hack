"""Built-in tools available to the agent."""
import os
import json
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from .config import get_settings

settings = get_settings()
DATA_DIR = Path(settings.agent_data_dir)


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a local file from the data directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filename inside the data directory"}
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file in the data directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files stored in the data directory.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Execute a simple Python expression and return the result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python expression to evaluate"}
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Return the current local date and time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


async def dispatch(name: str, args: dict) -> str:
    match name:
        case "read_file":
            return await _read_file(args["filename"])
        case "write_file":
            return await _write_file(args["filename"], args["content"])
        case "list_files":
            return _list_files()
        case "run_python":
            return _run_python(args["code"])
        case "get_datetime":
            return datetime.now().isoformat()
        case _:
            return f"Unknown tool: {name}"


async def _read_file(filename: str) -> str:
    _ensure_data_dir()
    path = DATA_DIR / Path(filename).name  # prevent path traversal
    if not path.exists():
        return f"File not found: {filename}"
    async with aiofiles.open(path) as f:
        return await f.read()


async def _write_file(filename: str, content: str) -> str:
    _ensure_data_dir()
    path = DATA_DIR / Path(filename).name
    async with aiofiles.open(path, "w") as f:
        await f.write(content)
    return f"Written {len(content)} chars to {filename}"


def _list_files() -> str:
    _ensure_data_dir()
    files = [f.name for f in DATA_DIR.iterdir() if f.is_file()]
    return json.dumps(files) if files else "[]"


def _run_python(code: str) -> str:
    try:
        result = eval(code, {"__builtins__": {"abs": abs, "len": len, "range": range, "sum": sum, "min": min, "max": max, "round": round}})
        return str(result)
    except Exception as e:
        return f"Error: {e}"
