"""Restore only the explicitly selected sample code snapshot; preserve evidence and databases."""

import argparse
import hashlib
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("snapshot", help="Snapshot file relative to minimax/, e.g. evidence/baseline/tasks.py")
args = parser.parse_args()
snapshot = (project_root / args.snapshot).resolve()
if not snapshot.is_relative_to(project_root) or not snapshot.is_file():
    raise SystemExit("Choose an existing snapshot inside minimax/")
target = project_root / "sample/tasks.py"
target.write_bytes(snapshot.read_bytes())
print("Restored sample/tasks.py; sha256=" + hashlib.sha256(target.read_bytes()).hexdigest())
print("Re-import the manifest before retrieving context. Saved evidence and task state were retained.")
