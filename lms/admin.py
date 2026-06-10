from django.contrib import admin

from lms.models import Course, CourseSubscription, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner")
    search_fields = ("name", "description", "owner__email")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course", "owner", "video_url")
    search_fields = ("name", "description", "video_url", "owner__email")
    list_filter = ("course",)


@admin.register(CourseSubscription)
class CourseSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "created_at")
    search_fields = ("user__email", "course__name")
    list_filter = ("created_at",)
