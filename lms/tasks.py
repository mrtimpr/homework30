from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from lms.models import Course


@shared_task
def send_course_update_email(course_id: int) -> int:
    """Отправить уведомление об обновлении курса всем подписчикам."""
    course = Course.objects.prefetch_related("subscriptions__user").get(pk=course_id)
    recipient_emails = [
        subscription.user.email
        for subscription in course.subscriptions.all()
        if subscription.user.email and subscription.user.is_active
    ]

    if not recipient_emails:
        return 0

    send_mail(
        subject=f"Обновление курса: {course.name}",
        message=(
            f"В курсе \"{course.name}\" появились обновления. "
            "Зайдите в личный кабинет, чтобы посмотреть новые материалы."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_emails,
        fail_silently=False,
    )

    course.last_notification_at = timezone.now()
    course.save(update_fields=["last_notification_at"])
    return len(recipient_emails)
