"""Capture the real integration checks and their reproducible environment."""

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sdd_context.common import ROOT, timestamp, write_json

command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "tests", "--junitxml=evidence/context-tests.xml"]
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
(ROOT / "evidence/context-tests.log").write_text(result.stdout + result.stderr, encoding="utf-8")
record = {
    "at": timestamp(), "command": command, "exit_code": result.returncode,
    "python": sys.version,
    "versions": {name: importlib.metadata.version(name) for name in ["powercontext", "PyMySQL", "pytest", "httpx"]},
}
write_json(ROOT / "evidence/context-tests.json", record)
print(result.stdout + result.stderr)
print(json.dumps(record, indent=2))
raise SystemExit(result.returncode)
