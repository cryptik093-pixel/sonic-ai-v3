"""Existing repository tests call clear(): isolate all collection-time storage."""
import os
import tempfile
from pathlib import Path

_storage = tempfile.TemporaryDirectory(prefix="sonic-tests-")
os.environ["SONIC_DB_PATH"] = str(Path(_storage.name) / "app.db")
os.environ["SONIC_EVENT_DB"] = str(Path(_storage.name) / "events.db")
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
for _key in ("SONIC_OPENAI_API_KEY", "OPENAI_API_KEY", "SONIC_SHOPIFY_ACCESS_TOKEN",
             "SONIC_SHOPIFY_SHOP_DOMAIN", "SONIC_SHOPIFY_WEBHOOK_SECRET", "SONIC_CONTROL_PLANE_TOKEN",
             "SONIC_OAUTH_ISSUER", "SONIC_OAUTH_JWKS_URL", "SONIC_PUBLIC_MCP_URL"):
    os.environ.pop(_key, None)


def pytest_sessionfinish(session, exitstatus):
    from sqlalchemy.orm import close_all_sessions
    from apps.api.database import engine
    close_all_sessions()
    engine.dispose()
    _storage.cleanup()
