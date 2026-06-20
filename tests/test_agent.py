"""Basic smoke tests — no network required."""
import pytest
import asyncio
from src.agent.tools import dispatch


@pytest.mark.asyncio
async def test_datetime_tool():
    result = await dispatch("get_datetime", {})
    assert "T" in result  # ISO format


@pytest.mark.asyncio
async def test_python_tool():
    result = await dispatch("run_python", {"code": "2 + 2"})
    assert result == "4"


@pytest.mark.asyncio
async def test_write_read_file(tmp_path, monkeypatch):
    import src.agent.tools as t
    monkeypatch.setattr(t, "DATA_DIR", tmp_path)
    await dispatch("write_file", {"filename": "note.txt", "content": "hello"})
    result = await dispatch("read_file", {"filename": "note.txt"})
    assert result == "hello"


@pytest.mark.asyncio
async def test_list_files(tmp_path, monkeypatch):
    import src.agent.tools as t
    monkeypatch.setattr(t, "DATA_DIR", tmp_path)
    await dispatch("write_file", {"filename": "a.txt", "content": "x"})
    result = await dispatch("list_files", {})
    assert "a.txt" in result
