from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone


@shared_task
def block_inactive_users() -> int:
    """Заблокируйте активных пользователей, которые не входили в систему более месяца."""
    User = get_user_model()
    threshold = timezone.now() - timedelta(days=30)
    queryset = User.objects.filter(is_active=True).filter(
        last_login__isnull=False,
        last_login__lt=threshold,
    )
    return queryset.update(is_active=False)
