"""Small HTTP bridge used by the Dify workflow.

The bridge deliberately keeps the Dify side simple: Dify sends one JSON object and
receives plain text. Durable history is delegated to PowerContext's memory API.
"""
from __future__ import annotations

import hashlib
import os
import random
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Dify PowerContext Adventure Bridge", version="1.0.0")


class AdventureRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: str = Field(min_length=1, max_length=128)


def _base_url() -> str:
    return os.getenv("POWERCONTEXT_URL", "http://127.0.0.1:8000").rstrip("/")


def _scope_id(user_id: str) -> str:
    # Stable, safe identifier; avoids putting arbitrary user text in a URL/body.
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:24]
    return f"dify-adventure-{digest}"


def _request(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = __import__("json").dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.getenv("POWERCONTEXT_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{_base_url()}{path}", data=body, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=20) as response:  # nosec B310 - configured service URL
            raw = response.read().decode("utf-8")
            return __import__("json").loads(raw) if raw else {}
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError(f"PowerContext request failed: {exc}") from exc


def _memory_text(result: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for hit in result.get("hits", []) or []:
        entry = hit.get("entry") or hit.get("memory") or hit
        text = entry.get("text") if isinstance(entry, dict) else None
        if text:
            texts.append(str(text))
    return texts[:5]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/dify/adventure", response_class=PlainTextResponse)
def adventure(request: AdventureRequest) -> str:
    scope_id = _scope_id(request.user_id)
    try:
        recalled = _request(
            "/v1/memory/search",
            {"scope_id": scope_id, "query": request.message, "limit": 5, "mode": "fts"},
        )
        memories = _memory_text(recalled)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    rng = random.Random(hashlib.sha256(request.message.encode()).digest())
    moods = ["披风突然发光", "远处响起一声很不专业的龙吼", "骰子自己滚出了一个 7", "旁白开始怀疑自己的职业选择"]
    mood = rng.choice(moods)
    history = "；".join(memories[-2:]) if memories else "这是这位玩家的第一段冒险。"
    reply = (
        f"🎲 NPC：你决定‘{request.message}’。{mood}！\n"
        f"我记得：{history}\n"
        "现在剧情进入隐藏支线：请继续输入下一步行动。"
    )
    try:
        _request(
            "/v1/memory/remember",
            {
                "scope_id": scope_id,
                "kind": "dify-adventure-turn",
                "text": f"玩家行动：{request.message}\nNPC 回复：{reply}",
                "reason": "Dify 离谱冒险 NPC 保存连续剧情",
            },
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return reply
