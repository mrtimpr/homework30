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

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курсы"

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

    def __str__(self) -> str:
        return self.name