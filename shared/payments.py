"""
payments.py — Razorpay integration helper.
Creates orders, verifies signatures, records in db.
"""
import hmac, hashlib, json
import razorpay
from shared.config import Config
from shared import db

client = razorpay.Client(
    auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET)
)

def create_order(amount_inr: float, booking_id: str, notes: dict = None) -> dict:
    """Create Razorpay order. amount_inr in rupees → converts to paise."""
    order = client.order.create({
        "amount":   int(amount_inr * 100),
        "currency": "INR",
        "receipt":  booking_id,
        "notes":    notes or {},
    })
    return order

def verify_payment(razorpay_order_id: str,
                   razorpay_payment_id: str,
                   razorpay_signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        Config.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)

def record_payment(booking_id: str, razorpay_order_id: str,
                   razorpay_payment_id: str, amount: float,
                   status: str = "captured") -> dict:
    return db.insert_one("payments", {
        "booking_id":          booking_id,
        "razorpay_order_id":   razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "amount":              amount,
        "status":              status,
    })
