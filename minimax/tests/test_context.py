"""Integration tests require real seekdb and PowerContext, without a model key."""

import asyncio
import json
import shutil
import subprocess
import sys
from uuid import uuid4

import pytest

from sdd_context.__main__ import build_context
from sdd_context.common import ROOT
from sdd_context.minimax_agent import MissingMiniMaxKey, modify, parse_edit
from sdd_context.store import import_documents, retrieve


@pytest.fixture
def project(tmp_path, monkeypatch):
    shutil.copytree(ROOT / "sample", tmp_path / "sample")
    monkeypatch.setenv("SEEKDB_DATABASE", "minimax_sdd_tests")
    import_documents(tmp_path, tmp_path / "sample/manifest.json")
    return tmp_path


def test_sql_retrieves_real_spec_code_and_tests_and_excludes_unrelated(project):
    result = retrieve(project, "TASK-001")
    assert {item["kind"] for item in result["sources"]} == {"spec", "code", "test"}
    assert len(result["sources"]) == result["database_query"]["row_count"] == 3
    for source in result["sources"]:
        assert source["content"] == (project / source["path"]).read_text(encoding="utf-8")
        assert source["line_end"] >= source["line_start"]
    other = retrieve(project, "EXPORT-001")
    assert [item["path"] for item in other["sources"]] == ["sample/specs/unrelated.md"]


def test_changed_spec_requires_reimport_then_returns_current_content(project):
    spec = project / "sample/specs/tasks.md"
    updated = spec.read_text(encoding="utf-8").replace("revision 1", "revision 2")
    updated = updated.replace("returns an empty list", "raises ValueError")
    spec.write_text(updated, encoding="utf-8")
    with pytest.raises(ValueError, match="re-import"):
        retrieve(project, "TASK-001")
    import_documents(project, project / "sample/manifest.json")
    result = retrieve(project, "TASK-001")
    content = next(item["content"] for item in result["sources"] if item["kind"] == "spec")
    assert "revision 2" in content
    assert "raises ValueError" in content
    assert "returns an empty list" not in content


def test_failed_import_does_not_remove_previous_data(project):
    manifest = project / "sample/manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["documents"][0]["path"] = "missing.md"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        import_documents(project, manifest)
    assert len(retrieve(project, "TASK-001")["sources"]) == 3


def test_unknown_task_is_not_a_fixed_answer(project):
    with pytest.raises(ValueError, match="Unknown task"):
        retrieve(project, "does-not-exist")


def test_real_powercontext_state_is_reused_by_a_new_cli_process(project, tmp_path):
    task_id = "STATE-" + uuid4().hex
    manifest_path = project / "sample/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["tasks"][0]["id"] = task_id
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    import_documents(project, manifest_path)
    empty = asyncio.run(build_context(project, task_id))
    assert empty["task_state"]["latest"] is None
    # Both commands are independent OS processes. No memory object is shared.
    save = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "sdd_context", "save-state", task_id,
         "--done", "reviewed exact-status specification",
         "--todo", "run MiniMax code modification", "--test-result", "baseline expected functional failure"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    output = tmp_path / "restored.json"
    subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "sdd_context", "--root", str(project), "--out", str(output), "context", task_id],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    saved = json.loads(save.stdout)
    restored = json.loads(output.read_text(encoding="utf-8"))["task_state"]
    assert restored["latest"]["state"] == saved["state"]
    assert restored["scope_id"] == saved["scope_id"]
    assert restored["latest"]["citation"]


def test_initial_context_reads_powercontext(project):
    context = asyncio.run(build_context(project, "TASK-001"))
    assert context["task_state"]["scope_id"]


def test_missing_key_blocks_only_the_real_model_step(tmp_path, monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    with pytest.raises(MissingMiniMaxKey, match="MINIMAX_API_KEY"):
        modify(tmp_path, {}, tmp_path / "model-evidence")
    assert not (tmp_path / "model-evidence").exists()


def test_agent_will_not_apply_an_edit_to_tests():
    with pytest.raises(ValueError, match="sample/tasks.py"):
        parse_edit(json.dumps({"path": "sample/tests/test_tasks.py", "content": "pass\n"}))


def test_agent_accepts_fenced_json_and_valid_python():
    visible, edit = parse_edit('```json\n{"path":"sample/tasks.py","content":"x = 1\\n"}\n```')
    assert edit["content"] == "x = 1\n"
    assert visible.startswith("```json")
