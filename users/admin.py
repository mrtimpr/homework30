from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.forms import CustomUserChangeForm, CustomUserCreationForm
from users.models import Payment, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Настройка отображения кастомного пользователя в админке."""

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "phone",
        "city",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "is_superuser",
    )
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "phone",
        "city",
    )
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                    "city",
                    "avatar",
                )
            },
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    readonly_fields = ("last_login", "date_joined")

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "phone",
                    "city",
                    "avatar",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "payment_date",
        "paid_course",
        "paid_lesson",
        "amount",
        "payment_method",
    )
    list_filter = (
        "payment_method",
        "paid_course",
        "paid_lesson",
        "payment_date",
    )
    search_fields = (
        "user__email",
        "paid_course__name",
        "paid_lesson__name",
    )
