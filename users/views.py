from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Payment, User
from users.permissions import IsOwnerPaymentOrStaff, IsSelfForWriteOrReadOnly
from users.serializers import (
    PaymentSerializer,
    UserPrivateSerializer,
    UserPublicSerializer,
    UserRegisterSerializer,
)

class UserRegisterAPIView(generics.CreateAPIView):
    """Публичная конечная точка для регистрации пользователей."""

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        """Создать пользователя и преобразовать конфликты дублирования email-адресов в ответ с кодом 400."""
        try:
            serializer.save()
        except IntegrityError as error:
            raise ValidationError(
                {"email": "Пользователь с таким email уже существует."}
            ) from error

class UserViewSet(viewsets.ModelViewSet):
    """CRUD-операции для пользователей с безопасным представлением публичного и приватного профиля."""

    queryset = User.objects.prefetch_related("payments").all()
    permission_classes = [IsAuthenticated, IsSelfForWriteOrReadOnly]

    def get_serializer_class(self):
        """Выберите сериализатор в зависимости от действия."""
        if self.action == "list":
            return UserPublicSerializer
        if self.action == "create":
            return UserPrivateSerializer
        return UserPrivateSerializer

    def retrieve(self, request, *args, **kwargs):
        """Возвращать полный профиль только для себя и сотрудников, публичный профиль — для остальных."""
        instance = self.get_object()
        is_own_profile = instance == request.user
        can_see_private = is_own_profile or request.user.is_staff or request.user.is_superuser
        serializer_class = UserPrivateSerializer if can_see_private else UserPublicSerializer
        serializer = serializer_class(instance, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Обновлять только собственный профиль текущего пользователя, если он не является сотрудником."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = UserPrivateSerializer(
            instance,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Удалить профиль пользователя в соответствии с правами доступа к объекту."""
        return super().destroy(request, *args, **kwargs)


class PaymentViewSet(viewsets.ModelViewSet):
    """CRUD-операции для платежей с ограничениями по владельцу."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsOwnerPaymentOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ("paid_course", "paid_lesson", "payment_method")
    ordering_fields = ("payment_date",)
    ordering = ("-payment_date",)

    def get_queryset(self):
        """Сотрудники видят все платежи, обычные пользователи — только свои."""
        queryset = Payment.objects.select_related(
            "user",
            "paid_course",
            "paid_lesson",
        )
        if self.request.user.is_staff or self.request.user.is_superuser:
            return queryset.all()
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Привязать новый платеж к текущему пользователю."""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Создать платеж и вернуть созданный объект."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


