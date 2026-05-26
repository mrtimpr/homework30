from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from users.models import Payment, User
from users.serializers import PaymentSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """CRUD для пользователя, включая редактирование профиля."""

    queryset = User.objects.all()
    serializer_class = UserSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """CRUD для платежей с фильтрацией и сортировкой."""

    queryset = Payment.objects.select_related(
        "user",
        "paid_course",
        "paid_lesson",
    ).all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = (
        "paid_course",
        "paid_lesson",
        "payment_method",
    )
    ordering_fields = ("payment_date",)
    ordering = ("-payment_date",)

