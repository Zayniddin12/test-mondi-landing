# Mondi — restoran landing (Yo'lda integratsiyasini sinash uchun)

- `frontend/` — Nuxt 3 (menyu, savat, buyurtma, kuzatuv)
- `backend/` — FastAPI. Yo'lda API'ga `INTEGRATION.md` bo'yicha so'rov yuboradi. Kalit faqat shu yerda.

## Ishga tushirish
```bash
# backend
cd backend && cp .env.example .env   # YOLDA_BASE_URL va YOLDA_KEY ni to'ldiring
.venv/bin/uvicorn app.main:app --port 8000
# frontend (boshqa terminal)
cd frontend && npm install && npm run dev   # http://localhost:3000
```
Backend alohida serverda bo'lsa: frontend uchun `BACKEND_URL=https://backend.example.com`.

## Sozlamalar (`backend/.env`)
| o'zgaruvchi | izoh |
|---|---|
| `YOLDA_BASE_URL` | `https://<yolda-server>/api/v1` |
| `YOLDA_KEY` | `yl_live_…` |
| `YOLDA_WEBHOOK_SECRET` | webhook imzosi uchun (ixtiyoriy) |
| `DEFAULT_DELIVERY_FEE` | koordinata yo'q bo'lganda yetkazish haqi |

Webhook URL (Yo'lda'ga berish): `https://<backend>/api/webhooks/yolda`

## Onlayn to'lov (docs/PAYMENTS.md)
To'lovni Tez-yetkaz (Multicard) qabul qiladi. Backend: `GET /api/payment-methods`, `POST /api/orders` (`payment_method`: `naqd` yoki usul kodi), `POST /api/orders/{id}/pay`, `GET /api/orders/{id}/payment`. Mijoz `pay_url` ga yo'naltiriladi, qaytgach `?order=ID` orqali kuzatuv davom etadi. Webhook: `payment.paid`.
