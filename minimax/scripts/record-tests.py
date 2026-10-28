"""Run the fixed business suite and record command, exit code, and exact source identity."""

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sdd_context.common import ROOT, digest, timestamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["baseline", "after"])
    args = parser.parse_args()
    directory = ROOT / "evidence" / args.phase
    directory.mkdir(parents=True, exist_ok=True)
    suite_path = ROOT / "sample/tests/test_tasks.py"
    suite_hash = hashlib.sha256(suite_path.read_bytes()).hexdigest()
    if args.phase == "after":
        baseline = json.loads((ROOT / "evidence/baseline/result.json").read_text(encoding="utf-8"))
        if baseline["test_sha256"] != suite_hash:
            raise RuntimeError("The target/regression tests changed since baseline")
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-rA", "--junitxml=" + str(directory / "junit.xml"),
               "sample/tests/test_tasks.py"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    (directory / "pytest.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    suites = ET.parse(directory / "junit.xml").getroot()
    cases = list(suites.iter("testcase"))
    failed = [case.get("name") for case in cases if case.find("failure") is not None]
    errors = [case.get("name") for case in cases if case.find("error") is not None]
    skipped = [case.get("name") for case in cases if case.find("skipped") is not None]
    git_result = subprocess.run(
        ["git", "-c", "safe.directory=" + ROOT.parent.as_posix(), "rev-parse", "HEAD"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
    )
    record = {
        "phase": args.phase, "at": timestamp(), "command": command, "exit_code": result.returncode,
        "git_head": git_result.stdout.strip(), "source_sha256": digest((ROOT / "sample/tasks.py").read_text(encoding="utf-8")),
        "test_sha256": suite_hash, "tests": len(cases), "failures": failed, "errors": errors, "skipped": skipped,
    }
    (directory / "tasks.py").write_bytes((ROOT / "sample/tasks.py").read_bytes())
    write_json(directory / "result.json", record)
    print(json.dumps(record, indent=2))
    valid = (result.returncode == 1 and failed and all(name.startswith("test_target_") for name in failed)
             if args.phase == "baseline" else result.returncode == 0 and not failed)
    if not valid or errors or skipped or len(cases) != 8:
        raise SystemExit("Business test evidence does not meet the expected phase")


if __name__ == "__main__":
    main()
