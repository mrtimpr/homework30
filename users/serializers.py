from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

    password = serializers.CharField(
        write_only=True,
        required=False,
    )

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

    def create(self, validated_data):
        """Создаёт пользователя с хешированным паролем."""
        password = validated_data.pop("password", None)
        user = User(**validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user

    def update(self, instance, validated_data):
        """Обновляет пользователя, при наличии пароля хеширует его."""
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
