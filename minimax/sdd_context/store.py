"""Actual SQL storage and retrieval. No in-memory or file search fallback."""

import json
import os
import re
from contextlib import contextmanager

import pymysql

from .common import digest, project_file


@contextmanager
def connect():
    database = os.environ.get("SEEKDB_DATABASE", "minimax_sdd")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", database):
        raise ValueError("SEEKDB_DATABASE must be a simple SQL identifier")
    connection = pymysql.connect(
        host=os.environ.get("SEEKDB_HOST", "127.0.0.1"),
        port=int(os.environ.get("SEEKDB_PORT", "2882")),
        user=os.environ.get("SEEKDB_USER", "root"),
        password=os.environ.get("SEEKDB_PASSWORD", ""),
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=5,
        read_timeout=30,
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
            cursor.execute(f"USE `{database}`")
        yield connection
    finally:
        connection.close()


def import_documents(root, manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Validate and read everything before modifying the previous index.
    documents = []
    for item in manifest["documents"]:
        text = project_file(root, item["path"]).read_text(encoding="utf-8")
        documents.append((item, text, digest(text)))
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("""CREATE TABLE IF NOT EXISTS sdd_documents (
            path VARCHAR(512) PRIMARY KEY, kind VARCHAR(16) NOT NULL,
            symbol VARCHAR(255) NOT NULL, content LONGTEXT NOT NULL,
            sha256 CHAR(64) NOT NULL)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sdd_terms (
            path VARCHAR(512) NOT NULL, term VARCHAR(128) NOT NULL,
            PRIMARY KEY (path, term), INDEX term_lookup (term))""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS sdd_tasks (
            task_id VARCHAR(128) PRIMARY KEY, description TEXT NOT NULL,
            terms_json TEXT NOT NULL)""")
        # These three tables belong only to this module's selected database.
        cursor.execute("DELETE FROM sdd_terms")
        cursor.execute("DELETE FROM sdd_documents")
        cursor.execute("DELETE FROM sdd_tasks")
        for item, text, sha256 in documents:
            cursor.execute(
                "INSERT INTO sdd_documents (path,kind,symbol,content,sha256) VALUES (%s,%s,%s,%s,%s)",
                (item["path"], item["kind"], item["symbol"], text, sha256),
            )
            for term in item["terms"]:
                cursor.execute("INSERT INTO sdd_terms (path,term) VALUES (%s,%s)", (item["path"], term))
        for task in manifest["tasks"]:
            cursor.execute(
                "INSERT INTO sdd_tasks (task_id,description,terms_json) VALUES (%s,%s,%s)",
                (task["id"], task["description"], json.dumps(task["terms"])),
            )
        connection.commit()
        cursor.execute("SELECT VERSION() AS version")
        return {"documents": len(documents), "tasks": len(manifest["tasks"]), "server": cursor.fetchone()}


def retrieve(root, task_id):
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT * FROM sdd_tasks WHERE task_id=%s", (task_id,))
        task = cursor.fetchone()
        if task is None:
            raise ValueError(f"Unknown task: {task_id}; import a manifest containing it first")
        terms = json.loads(task.pop("terms_json"))
        if not terms:
            raise ValueError("A task must have at least one retrieval term")
        placeholders = ",".join(["%s"] * len(terms))
        sql = f"""SELECT d.path,d.kind,d.symbol,d.content,d.sha256,COUNT(*) AS score
            FROM sdd_documents d JOIN sdd_terms t ON t.path=d.path
            WHERE t.term IN ({placeholders})
            GROUP BY d.path,d.kind,d.symbol,d.content,d.sha256
            ORDER BY score DESC,d.path"""
        cursor.execute(sql, terms)
        sources = cursor.fetchall()
        cursor.execute("SELECT VERSION() AS version")
        server = cursor.fetchone()
    for source in sources:
        current = project_file(root, source["path"]).read_text(encoding="utf-8")
        if digest(current) != source["sha256"]:
            raise ValueError(f"Source changed since import; re-import first: {source['path']}")
        source["line_start"] = 1
        source["line_end"] = len(source["content"].splitlines())
    return {
        "task": task,
        "sources": sources,
        "database_query": {"sql": sql, "parameters": terms, "row_count": len(sources), "server": server},
    }
