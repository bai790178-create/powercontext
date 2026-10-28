"""Task state is stored and loaded through the real PowerContext Python client."""

import json
import os

from powercontext.client import PowerContextClient
from powercontext.http import CreateScopeRequest, RememberMemoryRequest, SearchMemoryRequest

from .common import timestamp


async def task_scope(client, task_id):
    return await client.create_scope(CreateScopeRequest(
        title=f"MiniMax SDD {task_id}",
        summary="Task progress and verification results for the competition sample",
        idempotency_key=f"minimax-sdd:{task_id}",
    ))


async def read_state(task_id):
    async with PowerContextClient(os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8910")) as client:
        scope = await task_scope(client, task_id)
        response = await client.search_memory(SearchMemoryRequest(
            scope_id=scope.scope_id, query="sddtaskstate", mode="fts", limit=50,
        ))
        states = []
        for hit in response.hits:
            marker, separator, payload = hit.memory.text.partition("\n")
            if marker == "sddtaskstate" and separator:
                state = json.loads(payload)
                if state["task_id"] == task_id:
                    states.append({"state": state, "citation": hit.memory.artifact.model_dump(mode="json")})
        states.sort(key=lambda item: item["state"]["saved_at"], reverse=True)
        return {"scope_id": scope.scope_id, "latest": states[0] if states else None}


async def save_state(task_id, done, todo, tests):
    state = {"task_id": task_id, "done": done, "todo": todo, "tests": tests, "saved_at": timestamp()}
    async with PowerContextClient(os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8910")) as client:
        scope = await task_scope(client, task_id)
        response = await client.remember_memory(RememberMemoryRequest(
            scope_id=scope.scope_id,
            kind="progress",
            text="sddtaskstate\n" + json.dumps(state, ensure_ascii=False),
            reason="Persist task progress for use after the context module restarts",
        ))
        return {"scope_id": scope.scope_id, "state": state, "result": response.model_dump(mode="json")}
