from django.contrib import admin

from lms.models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админка курса."""

    list_display = ("id", "name")
    search_fields = ("name", "description")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админка урока."""

    list_display = ("id", "name", "course", "video_url")
    list_filter = ("course",)
    search_fields = ("name", "description", "video_url")