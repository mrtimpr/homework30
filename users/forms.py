from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from users.models import User


class CustomUserCreationForm(UserCreationForm):
    """Форма создания пользователя в админке."""

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "is_staff",
            "is_active",
            "is_superuser",
        )


class CustomUserChangeForm(UserChangeForm):
    """Форма изменения пользователя в админке."""

    class Meta:
        model = User
        fields = "__all__"