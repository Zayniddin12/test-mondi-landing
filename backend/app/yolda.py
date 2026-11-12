"""Yo'lda orders API klienti (INTEGRATION.md)."""
import asyncio
import hashlib
import hmac

import httpx

from .config import settings


class YoldaError(Exception):
    def __init__(self, status: int, detail: str, field: str | None = None):
        self.status, self.detail, self.field = status, detail, field


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.yolda_key}", "Content-Type": "application/json"}


async def call(method: str, path: str, *, json: dict | None = None, params: dict | None = None,
               retries: int = 3) -> tuple[int, dict]:
    if not settings.yolda_base_url or not settings.yolda_key:
        raise YoldaError(503, "Yo'lda integratsiyasi sozlanmagan (YOLDA_BASE_URL / YOLDA_KEY)")
    url = settings.yolda_base_url.rstrip("/") + path
    last: Exception | None = None
    async with httpx.AsyncClient(timeout=10) as client:
        for attempt in range(retries):
            try:
                r = await client.request(method, url, headers=_headers(), json=json, params=params)
            except httpx.HTTPError as e:  # timeout / tarmoq xatosi — external_id idempotent, qayta yuboramiz
                last = e
            else:
                if r.status_code < 500:
                    try:
                        body = r.json()
                    except ValueError:
                        body = {"detail": r.text[:200]}
                    if r.status_code >= 400:
                        raise YoldaError(r.status_code, str(body.get("detail", "Xato")), body.get("field"))
                    return r.status_code, body
                last = YoldaError(r.status_code, "Yo'lda serverida xato")
            await asyncio.sleep(1.5 * (attempt + 1))
    raise YoldaError(502, f"Yo'lda javob bermadi: {last}")


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    if not settings.yolda_webhook_secret:
        return False
    expected = "sha256=" + hmac.new(settings.yolda_webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")
