import stripe
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from models import SessionLocal, User
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': 'Premium-abonnement'},
                'unit_amount': 500,
                'recurring': {'interval': 'month'}
            },
            'quantity': 1
        }],
        mode='subscription',
        success_url="http://localhost:8000/success",
        cancel_url="http://localhost:8000/cancel"
    )
    return JSONResponse({"id": session.id})

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    except stripe.error.SignatureVerificationError:
        return JSONResponse({"error": "Invalid signature"}, status_code=400)

    if event["type"] == "checkout.session.completed":
        # Normaal zou je customer_email of metadata gebruiken
        print("Checkout session completed")

    return {"status": "success"}
