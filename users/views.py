from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
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
from users.services import create_checkout_for_payment, sync_payment_status_from_stripe


@extend_schema(
    tags=["auth"],
    summary="Регистрация пользователя",
    description="Создаёт пользователя. Эндпоинт доступен без JWT-токена.",
)
class UserRegisterAPIView(generics.CreateAPIView):
    """Публичная конечная точка для регистрации пользователей."""

    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        """Создать пользователя и преобразовать конфликты email в ответ 400."""
        try:
            serializer.save()
        except IntegrityError as error:
            raise ValidationError(
                {"email": "Пользователь с таким email уже существует."}
            ) from error


@extend_schema_view(
    list=extend_schema(tags=["users"], summary="Список пользователей"),
    retrieve=extend_schema(tags=["users"], summary="Профиль пользователя"),
    create=extend_schema(tags=["users"], summary="Создание пользователя"),
    update=extend_schema(tags=["users"], summary="Обновление пользователя"),
    partial_update=extend_schema(tags=["users"], summary="Частичное обновление пользователя"),
    destroy=extend_schema(tags=["users"], summary="Удаление пользователя"),
)
class UserViewSet(viewsets.ModelViewSet):
    """CRUD-операции для пользователей с безопасным профилем."""

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
        """Возвращать полный профиль только для себя и сотрудников."""
        instance = self.get_object()
        is_own_profile = instance == request.user
        can_see_private = is_own_profile or request.user.is_staff or request.user.is_superuser
        serializer_class = UserPrivateSerializer if can_see_private else UserPublicSerializer
        serializer = serializer_class(instance, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Обновлять профиль в соответствии с object permission."""
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
        """Удалить профиль пользователя в соответствии с object permission."""
        return super().destroy(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=["payments"], summary="Список платежей"),
    retrieve=extend_schema(tags=["payments"], summary="Детальная информация о платеже"),
    create=extend_schema(
        tags=["payments"],
        summary="Создание платежа и Stripe Checkout-сессии",
        description=(
            "Создаёт локальный платёж, затем создаёт в Stripe продукт, цену и "
            "Checkout Session. Поле amount передаётся в рублях, а в Stripe "
            "отправляется в копейках. В ответе возвращаются данные платежа "
            "и ссылка payment_link."
        ),
        responses={
            201: PaymentSerializer,
            400: OpenApiResponse(description="Ошибка валидации или ошибка Stripe"),
            401: OpenApiResponse(description="Пользователь не авторизован"),
        },
    ),
    update=extend_schema(tags=["payments"], summary="Обновление платежа"),
    partial_update=extend_schema(tags=["payments"], summary="Частичное обновление платежа"),
    destroy=extend_schema(tags=["payments"], summary="Удаление платежа"),
)
class PaymentViewSet(viewsets.ModelViewSet):
    """CRUD платежей и Stripe Checkout для оплаты курсов/уроков."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsOwnerPaymentOrStaff]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ("paid_course", "paid_lesson", "payment_method", "status")
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
        """Создать локальный платёж и связать его со Stripe Checkout."""
        payment = serializer.save(user=self.request.user)

        if payment.payment_method != Payment.PAYMENT_METHOD_STRIPE:
            return

        try:
            checkout_data = create_checkout_for_payment(payment)
        except ValidationError:
            payment.status = Payment.STATUS_CANCELED
            payment.save(update_fields=["status"])
            raise
        except Exception as error:
            payment.status = Payment.STATUS_CANCELED
            payment.save(update_fields=["status"])
            raise ValidationError({"stripe": str(error)}) from error

        payment.stripe_product_id = checkout_data.product_id
        payment.stripe_price_id = checkout_data.price_id
        payment.stripe_session_id = checkout_data.session_id
        payment.payment_link = checkout_data.payment_link
        payment.status = checkout_data.status
        payment.save(
            update_fields=[
                "stripe_product_id",
                "stripe_price_id",
                "stripe_session_id",
                "payment_link",
                "status",
            ]
        )

    @extend_schema(
        tags=["payments"],
        summary="Проверка статуса платежа в Stripe",
        description=(
            "Получает актуальный статус Stripe Checkout Session по stripe_session_id "
            "и синхронизирует статус платежа в базе данных."
        ),
        responses={
            200: PaymentSerializer,
            400: OpenApiResponse(
                description=(
                    "У платежа отсутствует stripe_session_id или Stripe вернул ошибку"
                )
            ),
            401: OpenApiResponse(description="Пользователь не авторизован"),
            404: OpenApiResponse(description="Платёж не найден"),
        },
    )
    @action(detail=True, methods=["get"], url_path="check-status")
    def check_status(self, request, pk=None):
        """Проверить статус Stripe Checkout Session."""
        payment = self.get_object()
        try:
            sync_payment_status_from_stripe(payment)
        except Exception as error:
            raise ValidationError({"stripe": str(error)}) from error
        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
