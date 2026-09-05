"""Local operator probe. Read provider configuration, persist redacted evidence.

Run from the repository root: .venv/Scripts/python.exe scripts/check_integrations.py
No credentials are accepted as command-line arguments or printed.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.integrations.config import ControlConfig
from apps.api.integrations.service import ControlPlane
from apps.api.integrations.store import EventStore


async def main():
    config = ControlConfig.from_env()
    plane = ControlPlane(config, EventStore(config.event_db))
    result = await plane.check()
    print(json.dumps(result, indent=2))
    providers = [x for x in result["integrations"] if x["provider"] in ("openai", "shopify")]
    return 0 if all(x["validation_status"] == "VALIDATED" for x in providers) else 2


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception:
        print('{"error": "local_probe_failed", "validation_status": "FAILED"}')
        sys.exit(1)
