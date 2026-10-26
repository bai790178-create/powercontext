from __future__ import annotations

import json
import os
from typing import Any

import pymysql
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="StepFun local seekdb bridge")


def connection():
    return pymysql.connect(
        host=os.getenv("SEEKDB_HOST", "127.0.0.1"),
        port=int(os.getenv("SEEKDB_PORT", "2881")),
        user=os.getenv("SEEKDB_USER", "root"),
        password=os.getenv("SEEKDB_PASSWORD", ""),
        database=os.getenv("SEEKDB_DATABASE", "test"),
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


class Document(BaseModel):
    id: str
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float]


class DocumentBatch(BaseModel):
    documents: list[Document]


class SearchRequest(BaseModel):
    query: str
    embedding: list[float]
    limit: int = Field(default=5, ge=1, le=20)


@app.get("/health")
def health():
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return {"ok": True, "backend": "seekdb"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"seekdb unavailable: {exc}") from exc


@app.post("/api/documents")
def add_documents(batch: DocumentBatch):
    if not batch.documents:
        return {"written": 0}
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO stepfun_documents (id, body, metadata, embedding) "
                "VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE body=VALUES(body), metadata=VALUES(metadata), embedding=VALUES(embedding)",
                [
                    (d.id, d.body, json.dumps(d.metadata, ensure_ascii=False), json.dumps(d.embedding))
                    for d in batch.documents
                ],
            )
        return {"written": len(batch.documents), "backend": "seekdb"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"seekdb write failed: {exc}") from exc


@app.post("/api/search")
def search(request: SearchRequest):
    vector = json.dumps(request.embedding)
    sql = """
        SELECT id, body, metadata,
               MATCH(body) AGAINST (%s IN NATURAL LANGUAGE MODE) AS lexical_score,
               l2_distance(embedding, %s) AS vector_distance
        FROM stepfun_documents
        ORDER BY (MATCH(body) AGAINST (%s IN NATURAL LANGUAGE MODE)
                  + 1.0 / (1.0 + l2_distance(embedding, %s))) DESC
        LIMIT %s
    """
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute(sql, (request.query, vector, request.query, vector, request.limit))
            rows = cur.fetchall()
        for row in rows:
            if isinstance(row.get("metadata"), str):
                row["metadata"] = json.loads(row["metadata"])
        return {"query": request.query, "results": rows, "backend": "seekdb", "hybrid": True}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"seekdb search failed: {exc}") from exc
