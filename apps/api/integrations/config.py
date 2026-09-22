import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from ..config import settings  # Retain the existing dotenv loading and OpenAI settings.


def scopes(value: str) -> tuple[str, ...]:
    return tuple(sorted(set(filter(None, re.split(r"[,\s]+", value)))))


@dataclass(frozen=True)
class ControlConfig:
    token: str = field(default="", repr=False)
    shop_domain: str = ""
    shop_token: str = field(default="", repr=False)
    webhook_secret: str = field(default="", repr=False)
    shop_version: str = "2026-07"
    requested_scopes: tuple[str, ...] = ()
    oauth_issuer: str = ""
    oauth_jwks_url: str = ""
    public_mcp_url: str = ""
    event_db: Path = Path(__file__).resolve().parents[1] / "storage" / "sonic_events.sqlite3"

    @classmethod
    def from_env(cls):
        return cls(
            token=os.getenv("SONIC_CONTROL_PLANE_TOKEN", ""),
            shop_domain=os.getenv("SONIC_SHOPIFY_SHOP_DOMAIN", "").strip().lower(),
            shop_token=os.getenv("SONIC_SHOPIFY_ACCESS_TOKEN", ""),
            webhook_secret=os.getenv("SONIC_SHOPIFY_WEBHOOK_SECRET", ""),
            shop_version=os.getenv("SONIC_SHOPIFY_API_VERSION") or "2026-07",
            requested_scopes=scopes(os.getenv("SONIC_SHOPIFY_REQUESTED_SCOPES", "")),
            oauth_issuer=os.getenv("SONIC_OAUTH_ISSUER", ""),
            oauth_jwks_url=os.getenv("SONIC_OAUTH_JWKS_URL", ""),
            public_mcp_url=os.getenv("SONIC_PUBLIC_MCP_URL", ""),
            event_db=Path(os.getenv("SONIC_EVENT_DB") or str(cls.event_db)).resolve(),
        )

    @property
    def valid_shop(self):
        return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*\.myshopify\.com", self.shop_domain))

    @property
    def oauth_requested(self):
        return bool(self.oauth_issuer or self.oauth_jwks_url or self.public_mcp_url)

    @property
    def oauth_configured(self):
        urls = [urlsplit(v) for v in (self.oauth_issuer, self.oauth_jwks_url, self.public_mcp_url)]
        return all(u.scheme == "https" and u.hostname and not u.username and not u.password
                   and not u.query and not u.fragment for u in urls) and urls[2].path == "/mcp"

    @property
    def auth_configured(self):
        return self.oauth_configured if self.oauth_requested else bool(self.token)
