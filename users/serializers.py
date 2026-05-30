from rest_framework import serializers

from lms.serializers import CourseSerializer, LessonSerializer
from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор платежа для списка платежей и CRUD-операций."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    paid_course_detail = CourseSerializer(source="paid_course", read_only=True)
    paid_lesson_detail = LessonSerializer(source="paid_lesson", read_only=True)
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
            "paid_course_detail",
            "paid_lesson",
            "paid_lesson_detail",
            "amount",
            "payment_method",
            "payment_method_display",
        )


class UserPaymentHistorySerializer(serializers.ModelSerializer):
    """Вложенный сериализатор истории платежей пользователя."""

    paid_course = CourseSerializer(read_only=True)
    paid_lesson = LessonSerializer(read_only=True)
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


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя с полной вложенной историей платежей."""

    password = serializers.CharField(
        write_only=True,
        required=False,
    )
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

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Обновляет пользователя, при наличии пароля хеширует его."""
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
