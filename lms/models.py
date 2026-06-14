from django.conf import settings
from django.db import models


class Course(models.Model):
    """Модель курса."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="владелец",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="название",
    )
    preview = models.ImageField(
        upload_to="lms/courses/previews/",
        blank=True,
        null=True,
        verbose_name="превью",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="описание",
    )
    price = models.PositiveIntegerField(
        default=0,
        verbose_name="цена курса",
    )

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курсы"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name


class Lesson(models.Model):
    """Модель урока."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="владелец",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="курс",
    )
    name = models.CharField(max_length=255, verbose_name="название")
    description = models.TextField(blank=True, null=True, verbose_name="описание")
    preview = models.ImageField(
        upload_to="lms/lessons/previews/",
        blank=True,
        null=True,
        verbose_name="превью",
    )
    video_url = models.URLField(max_length=500, verbose_name="ссылка на видео")

    class Meta:
        verbose_name = "урок"
        verbose_name_plural = "уроки"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.name


class CourseSubscription(models.Model):
    """Подписка пользователя на обновления курса."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_subscriptions",
        verbose_name="пользователь",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="курс",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="дата подписки")

    class Meta:
        verbose_name = "подписка на курс"
        verbose_name_plural = "подписки на курсы"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "course"),
                name="unique_user_course_subscription",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.course}"
