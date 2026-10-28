"""Loopback-only PowerContext server; explicit memory requires no model API."""

import os
from pathlib import Path

import uvicorn
from powercontext.builtin.persistence.sqlite import SQLiteConfig
from powercontext.builtin.runtime.config import InferenceConfig, RuntimeConfig
from powercontext.server.factory import create_server_app
from powercontext.server.settings import McpConfig, MetricsConfig, ServerSettings, TracingConfig

from .common import ROOT


def main():
    directory = Path(os.environ.get("SDD_STATE_DIR", ROOT / ".runtime" / "powercontext")).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    settings = ServerSettings(
        workspace=directory,
        database=SQLiteConfig(url=f"sqlite+aiosqlite:///{(directory / 'state.db').as_posix()}"),
        inference=InferenceConfig(),
        runtime=RuntimeConfig(schedule_seconds=None, experience_schedule_seconds=None),
        mcp=McpConfig(enabled=False),
        metrics=MetricsConfig(enabled=False),
        tracing=TracingConfig(enabled=False),
    )
    app = create_server_app(settings=settings, scheduler_path=directory / "scheduler.db")
    uvicorn.run(app, host="127.0.0.1", port=8910, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
