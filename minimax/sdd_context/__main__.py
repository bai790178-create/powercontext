import argparse
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from .common import ROOT, timestamp, write_json
from .state import read_state, save_state
from .store import import_documents, retrieve


async def build_context(root, task_id):
    context = retrieve(root, task_id)
    context["task_state"] = await read_state(task_id)
    context["generated_at"] = timestamp()
    return context


def main():
    load_dotenv(ROOT / ".env", override=False)
    parser = argparse.ArgumentParser(description="SDD task context: real seekdb + PowerContext")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import")
    importer.add_argument("--manifest", default="sample/manifest.json")
    context = commands.add_parser("context")
    context.add_argument("task_id")
    state = commands.add_parser("save-state")
    state.add_argument("task_id")
    state.add_argument("--done", action="append", default=[])
    state.add_argument("--todo", action="append", default=[])
    state.add_argument("--test-result", action="append", default=[])
    agent = commands.add_parser("modify")
    agent.add_argument("task_id")
    agent.add_argument("--evidence-dir", type=Path, default=ROOT / "evidence" / "minimax")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "import":
        result = import_documents(root, root / args.manifest)
    elif args.command == "context":
        result = asyncio.run(build_context(root, args.task_id))
    elif args.command == "save-state":
        result = asyncio.run(save_state(args.task_id, args.done, args.todo, args.test_result))
    else:
        from .minimax_agent import modify
        result = modify(root, asyncio.run(build_context(root, args.task_id)), args.evidence_dir)
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
