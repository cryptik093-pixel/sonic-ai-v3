"""Fixed, harmless provider reads. Never return provider error bodies or URLs."""
import re
from time import perf_counter
from urllib.parse import quote

import httpx

from ..config import Settings
from .config import ControlConfig
from .models import IntegrationStatus, now


def fail(status: IntegrationStatus, code: str, *, auth: bool | None = None):
    status.last_error = code
    status.authenticated = auth
    status.validation_status = "FAILED"
    return status


def http_failure(status: IntegrationStatus, response: httpx.Response) -> bool:
    status.reachable = True
    if not response.is_success:
        fail(status, f"provider_http_{response.status_code}", auth=False if response.status_code == 401 else None)
        return True
    return False


class OpenAIAdapter:
    def __init__(self, config: Settings):
        self.config = config

    def configuration(self):
        return IntegrationStatus(provider="openai", configured=bool(self.config.openai_api_key),
            validation_status="CONFIGURED" if self.config.openai_api_key else "NOT_CONFIGURED",
            degraded_capabilities=["inference_not_tested"])

    async def check(self, client: httpx.AsyncClient):
        status = self.configuration()
        status.checked_at = now()
        if not status.configured:
            status.last_error = "missing_api_key"
            return status
        # This check proves OpenAI, not an arbitrary compatible endpoint. Preserve
        # custom runtime configuration but never forward its key to a guessed host.
        if self.config.openai_base_url.rstrip("/") != "https://api.openai.com/v1":
            return fail(status, "non_official_base_url_not_validated")
        start = perf_counter()
        try:
            headers = {"Authorization": f"Bearer {self.config.openai_api_key}"}
            response = await client.get("https://api.openai.com/v1/models", headers=headers)
            if http_failure(status, response):
                return status
            data = response.json()
            if not isinstance(data.get("data"), list):
                return fail(status, "invalid_provider_response")
            status.authenticated = True
            status.evidence.append("Authenticated GET /v1/models succeeded")
            response = await client.get("https://api.openai.com/v1/models/" + quote(self.config.openai_model, safe=""), headers=headers)
            if not response.is_success:
                status.model_available = False if response.status_code in (403, 404) else None
                status.validation_status = "DEGRADED"
                status.last_error = f"model_http_{response.status_code}"
                return status
            if response.json().get("id") != self.config.openai_model:
                return fail(status, "invalid_model_response", auth=True)
            status.model_available = True
            status.validation_status = "VALIDATED"
            status.last_successful_check = status.checked_at
            status.evidence.append("Configured model metadata retrieved; inference availability remains untested")
            return status
        except httpx.RequestError:
            status.reachable = False if status.reachable is None else status.reachable
            return fail(status, "provider_transport_error", auth=status.authenticated)
        except (ValueError, KeyError, TypeError, AttributeError):
            return fail(status, "invalid_provider_response", auth=status.authenticated)
        finally:
            status.latency_ms = round((perf_counter() - start) * 1000, 2)


def compare_scopes(requested, granted, required):
    # Shopify write scopes imply the corresponding read scope.
    effective = set(granted) | {"read_" + x[6:] for x in granted if x.startswith("write_")}
    return sorted(set(required) - effective), sorted(set(requested) - effective)


class ShopifyAdapter:
    REQUIRED_SCOPES = ("read_products",)
    QUERY = "query SonicHealth { shop { id myshopifyDomain } currentAppInstallation { accessScopes { handle } } }"

    def __init__(self, config: ControlConfig):
        self.config = config

    def configuration(self):
        configured = bool(self.config.shop_token and self.config.valid_shop)
        return IntegrationStatus(provider="shopify", configured=configured,
            api_version=self.config.shop_version, requested_scopes=list(self.config.requested_scopes),
            required_scopes=list(self.REQUIRED_SCOPES),
            validation_status="CONFIGURED" if configured else "NOT_CONFIGURED",
            degraded_capabilities=["live_mutations_disabled", "webhook_delivery_not_tested"])

    async def check(self, client: httpx.AsyncClient):
        status = self.configuration()
        status.checked_at = now()
        if not status.configured:
            status.last_error = "missing_or_invalid_shop_configuration"
            return status
        if self.config.shop_version != "2026-07":
            return fail(status, "unvalidated_api_version")
        start = perf_counter()
        try:
            url = f"https://{self.config.shop_domain}/admin/api/{self.config.shop_version}/graphql.json"
            headers = {"X-Shopify-Access-Token": self.config.shop_token}
            response = await client.post(url, headers=headers, json={"query": self.QUERY})
            if http_failure(status, response):
                return status
            data = response.json()
            if data.get("errors"):
                return fail(status, "graphql_errors")
            result = data["data"]
            if result["shop"]["myshopifyDomain"].lower() != self.config.shop_domain:
                return fail(status, "shop_identity_mismatch")
            if not result["shop"]["id"]:
                return fail(status, "invalid_shop_identity")
            granted = result["currentAppInstallation"]["accessScopes"]
            if not isinstance(granted, list) or any(not re.fullmatch(r"[a-z_]+", x["handle"]) for x in granted):
                return fail(status, "invalid_scope_response")
            status.authenticated = True
            status.granted_scopes = sorted({s["handle"] for s in granted})
            status.missing_scopes, status.ungranted_requested_scopes = compare_scopes(
                status.requested_scopes, status.granted_scopes, status.required_scopes)
            status.permissions_proven = not status.missing_scopes
            status.evidence.append("Shop identity and installed application scopes retrieved")
            if response.headers.get("X-Shopify-API-Version") != self.config.shop_version:
                status.last_error = "api_version_not_confirmed"
            elif status.missing_scopes:
                status.last_error = "missing_required_scopes"
            else:
                # A granted scope is not itself an end-to-end read test.
                response = await client.post(url, headers=headers, json={"query": "query SonicProductRead { products(first: 1) { nodes { id } } }"})
                if not response.is_success or response.json().get("errors"):
                    status.last_error = "product_read_failed"
                elif not isinstance(response.json()["data"]["products"]["nodes"], list):
                    status.last_error = "invalid_product_response"
                else:
                    status.evidence.append("Minimal products query succeeded; product data not retained")
            status.validation_status = "DEGRADED" if status.last_error else "VALIDATED"
            if not status.last_error:
                status.last_successful_check = status.checked_at
            return status
        except httpx.RequestError:
            status.reachable = False if status.reachable is None else status.reachable
            return fail(status, "provider_transport_error", auth=status.authenticated)
        except (ValueError, KeyError, TypeError, AttributeError):
            return fail(status, "invalid_provider_response", auth=status.authenticated)
        finally:
            status.latency_ms = round((perf_counter() - start) * 1000, 2)

    def apply(self, *args, **kwargs):
        raise PermissionError("Live mutations disabled; an approved proposal and verified execution workflow are required")
