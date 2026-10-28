import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from powercontext.client import PowerContextClient
from dotenv import load_dotenv
from sdd_context.common import ROOT
from sdd_context.store import connect

load_dotenv(ROOT / ".env", override=False)


async def check():
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT VERSION() AS version, 1+1 AS arithmetic")
        database = cursor.fetchone()
        assert database["arithmetic"] == 2
    async with PowerContextClient(os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8910")) as client:
        capabilities = await client.get_capabilities()
    print(json.dumps({"seekdb": database, "powercontext": capabilities.model_dump(mode="json")}, indent=2))


asyncio.run(check())
