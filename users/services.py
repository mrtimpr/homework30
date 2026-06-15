from __future__ import annotations

from dataclasses import dataclass

import stripe
from django.conf import settings
from rest_framework.exceptions import ValidationError

from users.models import Payment


@dataclass(frozen=True)
class StripeCheckoutData:
    """Нормализованные объекты Stripe, необходимые приложению."""

    product_id: str
    price_id: str
    session_id: str
    payment_link: str
    status: str


def _configure_stripe() -> None:
    """Настройте SDK Stripe с помощью параметров проекта."""
    stripe.api_key = settings.STRIPE_API_KEY


def _get_payment_product_name(payment: Payment) -> str:
    """Возвращаемое название продукта для платного курса или урока."""
    if payment.paid_course:
        return payment.paid_course.name
    if payment.paid_lesson:
        return payment.paid_lesson.name
    raise ValidationError({"payment": "Укажите курс или урок для оплаты."})


def _get_payment_amount(payment: Payment) -> int:
    """Сумма возврата платежа указана в наименьшей валютной единице."""
    if payment.amount <= 0:
        raise ValidationError({"amount": "Сумма оплаты должна быть больше нуля."})
    return int(payment.amount) * 100


def normalize_stripe_status(session: dict) -> str:
    """Сопоставьте статусы сессий оформления заказа Stripe со статусами локальных платежей."""
    payment_status = session.get("payment_status")
    session_status = session.get("status")

    if payment_status == "paid":
        return Payment.STATUS_PAID
    if payment_status == "unpaid":
        return Payment.STATUS_UNPAID
    if payment_status == "no_payment_required":
        return Payment.STATUS_PAID
    if session_status == "open":
        return Payment.STATUS_OPEN
    if session_status == "complete":
        return Payment.STATUS_PAID
    if session_status == "expired":
        return Payment.STATUS_CANCELED

    return Payment.STATUS_OPEN


def create_stripe_product(payment: Payment) -> dict:
    """Создайте продукт Stripe для оплаты курса или урока."""
    _configure_stripe()
    product_name = _get_payment_product_name(payment)

    try:
        product = stripe.Product.create(
            name=product_name,
            metadata={"payment_id": str(payment.pk)},
        )
    except stripe.error.StripeError as error:
        raise ValidationError(
            {"stripe": f"Ошибка создания продукта Stripe: {error}"}
        ) from error

    return product


def create_stripe_price(payment: Payment, product_id: str) -> dict:
    """Создайте цену Stripe для указанного товара."""
    _configure_stripe()

    try:
        price = stripe.Price.create(
            currency=settings.STRIPE_CURRENCY,
            unit_amount=_get_payment_amount(payment),
            product=product_id,
            metadata={"payment_id": str(payment.pk)},
        )
    except stripe.error.StripeError as error:
        raise ValidationError(
            {"stripe": f"Ошибка создания цены Stripe: {error}"}
        ) from error

    return price


def create_stripe_checkout_session(payment: Payment, price_id: str) -> dict:
    """Создайте сессию Stripe Checkout и верните её данные."""
    _configure_stripe()

    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            client_reference_id=str(payment.pk),
            metadata={"payment_id": str(payment.pk)},
        )
    except stripe.error.StripeError as error:
        raise ValidationError(
            {"stripe": f"Ошибка создания Stripe Checkout Session: {error}"}
        ) from error

    return session


def create_checkout_for_payment(payment: Payment) -> StripeCheckoutData:
    """Создайте в Stripe информацию о товаре, цене и сессии оформления заказа для локальной оплаты."""
    product = create_stripe_product(payment)
    price = create_stripe_price(payment, product["id"])
    session = create_stripe_checkout_session(payment, price["id"])

    return StripeCheckoutData(
        product_id=product["id"],
        price_id=price["id"],
        session_id=session["id"],
        payment_link=session["url"],
        status=normalize_stripe_status(session),
    )


def retrieve_checkout_session(session_id: str) -> dict:
    """Получить данные сессии Stripe Checkout по id."""
    if not session_id:
        raise ValidationError({"stripe": "У платежа нет Stripe session id."})

    _configure_stripe()

    try:
        return stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as error:
        raise ValidationError(
            {"stripe": f"Ошибка получения статуса Stripe-сессии: {error}"}
        ) from error


def sync_payment_status_from_stripe(payment: Payment) -> dict:
    """Получить сессию Stripe и обновить локальный статус платежа."""
    session = retrieve_checkout_session(payment.stripe_session_id)
    payment.status = normalize_stripe_status(session)
    payment.save(update_fields=["status"])
    return session
