from rest_framework import serializers

from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "user",
            "user_email",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "payment_method_display",
        )
        read_only_fields = ("id", "user", "user_email", "payment_date")


class UserPaymentHistorySerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для истории платежей владельца."""

    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "amount",
            "payment_method",
            "payment_method_display",
        )


class UserPublicSerializer(serializers.ModelSerializer):
    """Сериализатор публичного профиля для просмотра профиля другого пользователя."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "phone",
            "city",
            "avatar",
        )
        read_only_fields = fields


class UserPrivateSerializer(serializers.ModelSerializer):
    """Сериализатор приватного профиля для владельца профиля."""

    password = serializers.CharField(write_only=True, required=False)
    payments = UserPaymentHistorySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "payments",
        )
        read_only_fields = ("id", "payments")

    def create(self, validated_data):
        """Создайте пользователя и хешируйте пароль."""
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Обновить пользователя и хешировать пароль, если он предоставлен."""
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для публичной регистрации пользователей."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
        )
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        """Отклонять дубликаты email-адресов до срабатывания ограничения базы данных."""
        normalized_email = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return normalized_email

    def create(self, validated_data):
        """Создать обычного активного пользователя."""
        return User.objects.create_user(**validated_data)
