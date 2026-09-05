"""Fail-closed operator boundary for the local MCP loop and control endpoints."""
import hmac
import asyncio
from functools import lru_cache
from urllib.parse import urlsplit
import jwt
from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from .config import ControlConfig


@lru_cache(maxsize=4)
def jwks_client(url: str):
    return jwt.PyJWKClient(url, timeout=8)


def verify_oauth(token: str, config: ControlConfig):
    key = jwks_client(config.oauth_jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(token, key.key, algorithms=["RS256"], issuer=config.oauth_issuer,
        audience=config.public_mcp_url, options={"require": ["exp", "iat", "sub", "aud", "iss"]})


class ControlPlaneAuth:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if path == "/integrations/shopify/webhooks":
            # Shopify authenticates with raw-body HMAC, never the operator token.
            return await self.app(scope, receive, send)
        if scope["type"] != "http" or not (path == "/mcp" or path.startswith("/mcp/") or path == "/integrations" or path.startswith("/integrations/")):
            return await self.app(scope, receive, send)
        config = ControlConfig.from_env()
        if not config.auth_configured:
            return await JSONResponse({"detail": "control_plane_auth_not_configured"}, 503)(scope, receive, send)
        headers = Headers(scope=scope)
        parts = headers.get("authorization", "").split(" ", 1)
        valid = len(parts) == 2 and parts[0].lower() == "bearer"
        challenge = 'Bearer realm="sonic-operator"'
        if config.oauth_configured:
            origin = urlsplit(config.public_mcp_url)
            metadata = f"{origin.scheme}://{origin.netloc}/.well-known/oauth-protected-resource/mcp"
            challenge = f'Bearer resource_metadata="{metadata}", scope="sonic:read"'
            if valid:
                try:
                    claims = await asyncio.to_thread(verify_oauth, parts[1], config)
                    granted = claims.get("scope", "")
                    required = "sonic:check" if path == "/integrations/check" else "sonic:read"
                    if not isinstance(granted, str) or required not in granted.split():
                        return await JSONResponse({"detail": "insufficient_scope"}, 403)(scope, receive, send)
                except (jwt.PyJWTError, ValueError, OSError):
                    valid = False
        elif valid:
            valid = hmac.compare_digest(parts[1].encode(), config.token.encode())
        if not valid:
            return await JSONResponse({"detail": "unauthorized"}, 401,
                headers={"WWW-Authenticate": challenge})(scope, receive, send)
        # Browsers are not control-plane clients; reject unsolicited Origin.
        if headers.get("origin"):
            return await JSONResponse({"detail": "origin_not_allowed"}, 403)(scope, receive, send)
        await self.app(scope, receive, send)
