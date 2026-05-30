from rest_framework import serializers

from lms.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    class Meta:
        model = Lesson
        fields = "__all__"


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса с количеством уроков и списком уроков."""

    lesson_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "name",
            "preview",
            "description",
            "lesson_count",
            "lessons",
        )

    def get_lesson_count(self, obj: Course) -> int:
        """Возвращает количество уроков курса."""
        return obj.lessons.count()
