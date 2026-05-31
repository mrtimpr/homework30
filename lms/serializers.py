from rest_framework import serializers

from lms.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)

    class Meta:
        model = Lesson
        fields = (
            "id",
            "owner",
            "owner_email",
            "course",
            "name",
            "description",
            "preview",
            "video_url",
        )
        read_only_fields = ("id", "owner", "owner_email")

    def validate_course(self, course: Course) -> Course:
        """Для обычных пользователей разрешить доступ к урокам только в рамках их собственных курсов."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            user = request.user
            is_admin = user.is_staff or user.is_superuser
            if not is_admin and not is_moderator(user) and course.owner_id != user.id:
                raise serializers.ValidationError(
                    "Нельзя добавить урок в чужой курс."
                )
        return course


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса с количеством уроков и списком уроков."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    lesson_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "owner",
            "owner_email",
            "name",
            "preview",
            "description",
            "lesson_count",
            "lessons",
        )
        read_only_fields = ("id", "owner", "owner_email", "lesson_count", "lessons")

    def get_lesson_count(self, obj: Course) -> int:
        """Возвращает количество уроков курса."""
        return obj.lessons.count()
