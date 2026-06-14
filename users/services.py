"""Service functions for Stripe payments."""

from __future__ import annotations

from dataclasses import dataclass

import stripe
from django.conf import settings
from rest_framework.exceptions import ValidationError

from users.models import Payment


@dataclass(frozen=True)
class StripeCheckoutData:
    """Normalized Stripe objects needed by the application."""

    product_id: str
    price_id: str
    session_id: str
    payment_link: str
    status: str


def _configure_stripe() -> None:
    """Configure Stripe SDK with project settings."""
    stripe.api_key = settings.STRIPE_API_KEY


def _get_payment_product_name(payment: Payment) -> str:
    """Return product name for the paid course or lesson."""
    if payment.paid_course:
        return payment.paid_course.name
    if payment.paid_lesson:
        return payment.paid_lesson.name
    raise ValidationError("Укажите курс или урок для оплаты.")


def _get_payment_amount(payment: Payment) -> int:
    """Return payment amount in the smallest currency unit."""
    if payment.amount <= 0:
        raise ValidationError("Сумма оплаты должна быть больше нуля.")
    return int(payment.amount) * 100


def create_stripe_product(payment: Payment) -> dict:
    """Create a Stripe product for a course or lesson payment."""
    _configure_stripe()
    product_name = _get_payment_product_name(payment)
    product = stripe.Product.create(
        name=product_name,
        metadata={"payment_id": str(payment.pk)},
    )
    return product


def create_stripe_price(payment: Payment, product_id: str) -> dict:
    """Create a Stripe price for the given product."""
    _configure_stripe()
    price = stripe.Price.create(
        currency=settings.STRIPE_CURRENCY,
        unit_amount=_get_payment_amount(payment),
        product=product_id,
        metadata={"payment_id": str(payment.pk)},
    )
    return price


def create_stripe_checkout_session(payment: Payment, price_id: str) -> dict:
    """Create a Stripe Checkout Session and return its data."""
    _configure_stripe()
    session = stripe.checkout.Session.create(
        line_items=[{"price": price_id, "quantity": 1}],
        mode="payment",
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=str(payment.pk),
        metadata={"payment_id": str(payment.pk)},
    )
    return session


def create_checkout_for_payment(payment: Payment) -> StripeCheckoutData:
    """Create product, price and checkout session in Stripe for a local payment."""
    product = create_stripe_product(payment)
    price = create_stripe_price(payment, product["id"])
    session = create_stripe_checkout_session(payment, price["id"])
    return StripeCheckoutData(
        product_id=product["id"],
        price_id=price["id"],
        session_id=session["id"],
        payment_link=session["url"],
        status=session.get("payment_status") or session.get("status") or Payment.STATUS_OPEN,
    )


def retrieve_checkout_session(session_id: str) -> dict:
    """Retrieve Stripe Checkout Session by id."""
    if not session_id:
        raise ValidationError("У платежа нет Stripe session id.")
    _configure_stripe()
    return stripe.checkout.Session.retrieve(session_id)


def sync_payment_status_from_stripe(payment: Payment) -> dict:
    """Retrieve Stripe session and update local payment status."""
    session = retrieve_checkout_session(payment.stripe_session_id)
    payment_status = session.get("payment_status") or session.get("status")
    if payment_status:
        payment.status = payment_status
        payment.save(update_fields=["status"])
    return session
