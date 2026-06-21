from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone



class UserManager(BaseUserManager):
    """Менеджер пользователя с авторизацией по email."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        """Создаёт пользователя с email и паролем."""
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Создаёт обычного пользователя."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """Создаёт суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser должен иметь is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser должен иметь is_superuser=True")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Кастомный пользователь с авторизацией по email."""

    email = models.EmailField(
        unique=True,
        verbose_name="email",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="имя",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="фамилия",
    )
    phone = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        verbose_name="телефон",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="город",
    )
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="аватарка",
    )

    is_staff = models.BooleanField(
        default=False,
        verbose_name="статус персонала",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="активен",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name="дата регистрации",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self) -> str:
        return self.email


class Payment(models.Model):
    """Модель платежа пользователя за курс или урок."""

    PAYMENT_METHOD_CASH = "cash"
    PAYMENT_METHOD_TRANSFER = "transfer"
    PAYMENT_METHOD_STRIPE = "stripe"

    STATUS_CREATED = "created"
    STATUS_OPEN = "open"
    STATUS_PAID = "paid"
    STATUS_UNPAID = "unpaid"
    STATUS_CANCELED = "canceled"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_CASH, "наличные"),
        (PAYMENT_METHOD_TRANSFER, "перевод на счет"),
        (PAYMENT_METHOD_STRIPE, "Stripe"),
    ]

    STATUS_CHOICES = [
        (STATUS_CREATED, "создан"),
        (STATUS_OPEN, "ожидает оплаты"),
        (STATUS_PAID, "оплачен"),
        (STATUS_UNPAID, "не оплачен"),
        (STATUS_CANCELED, "отменён"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="пользователь",
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="дата оплаты",
    )
    paid_course = models.ForeignKey(
        "lms.Course",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="payments",
        verbose_name="оплаченный курс",
    )
    paid_lesson = models.ForeignKey(
        "lms.Lesson",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="payments",
        verbose_name="оплаченный урок",
    )
    amount = models.PositiveIntegerField(
        verbose_name="сумма оплаты",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_METHOD_STRIPE,
        verbose_name="способ оплаты",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="статус платежа",
    )
    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID продукта Stripe",
    )
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID цены Stripe",
    )
    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID сессии Stripe",
    )
    payment_link = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        verbose_name="ссылка на оплату",
    )

    class Meta:
        verbose_name = "платёж"
        verbose_name_plural = "платежи"
        ordering = ("-payment_date",)

    def __str__(self) -> str:
        return f"{self.user.email}: {self.amount}"
