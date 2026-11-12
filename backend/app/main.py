import json
import logging
import secrets
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import menu, yolda
from .config import settings

log = logging.getLogger("mondi")
app = FastAPI(title="Mondi backend")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","),
                   allow_methods=["*"], allow_headers=["*"])

CASH = "naqd"
# Webhook orqali kelgan oxirgi holatlar (external_id -> event)
webhook_events: dict[str, dict] = {}


class CartLine(BaseModel):
    id: str
    qty: int = Field(ge=1, le=50)


class Customer(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r"^\+998\d{9}$")


class Address(BaseModel):
    text: str = Field(min_length=5, max_length=300)
    district: str | None = Field(default=None, max_length=100)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)


class OrderIn(BaseModel):
    customer: Customer
    address: Address
    items: list[CartLine] = Field(min_length=1)
    # "naqd" yoki /api/payment-methods dagi usul kodi (card, payme, click, uzum…)
    payment_method: str = Field(min_length=2, max_length=30)
    note: str | None = Field(default=None, max_length=500)
    lang: str = Field(default="uz", pattern=r"^(uz|ru|en)$")
    return_url: str | None = Field(default=None, max_length=500)
    return_error_url: str | None = Field(default=None, max_length=500)


def _fail(e: yolda.YoldaError):
    # Kalit xatosi mijozga emas, sozlash muammosi: 401 ni 502 qilib qaytaramiz
    status = 502 if e.status == 401 else e.status
    detail = "Yo'lda API kaliti noto'g'ri yoki yo'q (backend sozlamasi)" if e.status == 401 else e.detail
    raise HTTPException(status, detail)


@app.get("/api/menu")
def get_menu():
    return {"categories": menu.CATEGORIES, "items": menu.ITEMS}


@app.get("/api/health")
def health():
    return {"ok": True, "yolda_configured": bool(settings.yolda_base_url and settings.yolda_key)}


@app.get("/api/quote")
async def quote(lat: float, lng: float):
    try:
        _, body = await yolda.call("GET", "/quote", params={"lat": lat, "lng": lng}, retries=1)
    except yolda.YoldaError as e:
        _fail(e)
    return body


@app.get("/api/payment-methods")
async def payment_methods():
    """Onlayn to'lov usullari (Tez-yetkaz serverida boshqariladi). Bo'sh ro'yxat — onlayn to'lov yoqilmagan."""
    try:
        _, body = await yolda.call("GET", "/payment-methods", retries=1)
    except yolda.YoldaError as e:
        log.warning("payment-methods olinmadi: %s %s", e.status, e.detail)
        return {"methods": []}
    return {"methods": body.get("methods", [])}


@app.post("/api/orders", status_code=201)
async def create_order(order: OrderIn):
    method = order.payment_method.lower()
    if method != CASH:
        # Usul kodi serverdagi ro'yxatda bo'lishi shart
        codes = {m.get("code") for m in (await payment_methods())["methods"]}
        if method not in codes:
            raise HTTPException(422, "To'lov usuli noto'g'ri yoki onlayn to'lov yoqilmagan")

    items = []
    for line in order.items:
        item = menu.BY_ID.get(line.id)
        if not item:
            raise HTTPException(422, f"Noma'lum taom: {line.id}")
        items.append({"name": item["name"], "qty": line.qty, "price": item["price"]})

    external_id = f"MONDI-{int(time.time()):x}{secrets.token_hex(2)}".upper()
    payload: dict = {
        "external_id": external_id,
        "customer": order.customer.model_dump(),
        "address": {k: v for k, v in order.address.model_dump().items() if v is not None},
        "items": items,
        "payment": {"method": "Naqd"} if method == CASH else {"method": "Multicard", "system": method},
    }
    if method != CASH:
        # return_url dagi {ID} o'rniga buyurtma raqami qo'yiladi (docs: /pay bilan bir xil maydonlar)
        payload["payment"]["lang"] = order.lang
        for key in ("return_url", "return_error_url"):
            val = getattr(order, key)
            if val:
                payload["payment"][key] = val.replace("{ID}", external_id)
    if order.note:
        payload["note"] = order.note
    if order.address.lat is None or order.address.lng is None:
        payload["delivery_fee"] = settings.default_delivery_fee  # koordinata yo'q bo'lsa majburiy

    try:
        status, body = await yolda.call("POST", "/orders", json=payload)
    except yolda.YoldaError as e:
        log.warning("Yo'lda rad etdi: %s %s", e.status, e.detail)
        _fail(e)
    return {**body, "http_status": status}


class PayIn(BaseModel):
    method: str = Field(min_length=2, max_length=30)
    lang: str = Field(default="uz", pattern=r"^(uz|ru|en)$")
    return_url: str | None = Field(default=None, max_length=500)
    return_error_url: str | None = Field(default=None, max_length=500)


@app.post("/api/orders/{external_id}/pay")
async def pay_order(external_id: str, data: PayIn):
    """To'lov havolasini yaratadi/qaytaradi (usulni almashtirish yoki qayta urinish uchun). Idempotent."""
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    try:
        _, body = await yolda.call("POST", f"/orders/{external_id}/pay", json=payload, retries=2)
    except yolda.YoldaError as e:
        _fail(e)
    return body


@app.get("/api/orders/{external_id}/payment")
async def order_payment(external_id: str):
    try:
        _, body = await yolda.call("GET", f"/orders/{external_id}/payment", retries=1)
    except yolda.YoldaError as e:
        _fail(e)
    return body


@app.get("/api/orders/{external_id}")
async def order_status(external_id: str):
    try:
        _, body = await yolda.call("GET", f"/orders/{external_id}", retries=1)
    except yolda.YoldaError as e:
        _fail(e)
    return body


class CancelIn(BaseModel):
    reason: str = Field(default="Mijoz bekor qildi", max_length=200)


@app.post("/api/orders/{external_id}/cancel")
async def cancel_order(external_id: str, data: CancelIn):
    try:
        _, body = await yolda.call("POST", f"/orders/{external_id}/cancel", json={"reason": data.reason}, retries=1)
    except yolda.YoldaError as e:
        _fail(e)
    return body


@app.post("/api/webhooks/yolda")
async def yolda_webhook(request: Request):
    raw = await request.body()
    if not yolda.verify_signature(raw, request.headers.get("X-Yolda-Signature")):
        raise HTTPException(401, "Imzo noto'g'ri")
    event = json.loads(raw)
    webhook_events[event.get("external_id", "?")] = event
    log.info("Webhook: %s %s -> %s", event.get("event", "status"), event.get("external_id"),
             event.get("pay_status") or event.get("status"))
    return {"ok": True}
