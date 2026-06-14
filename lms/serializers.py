from rest_framework import serializers

from lms.models import Course, CourseSubscription, Lesson
from lms.permissions import is_moderator
from lms.validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    video_url = serializers.URLField(validators=[validate_youtube_url])

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
        """Разрешить добавление урока только в свой курс, сотруднику или модератору."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return course

        user = request.user

        if course.owner_id == user.id:
            return course

        if user.is_staff or user.is_superuser:
            return course

        if is_moderator(user):
            return course

        raise serializers.ValidationError("Нельзя добавить урок в чужой курс.")


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса с количеством уроков, списком уроков и признаком подписки."""

    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    lesson_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "owner",
            "owner_email",
            "name",
            "preview",
            "description",
            "price",
            "lesson_count",
            "lessons",
            "is_subscribed",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_email",
            "lesson_count",
            "lessons",
            "is_subscribed",
        )

    def get_lesson_count(self, obj: Course) -> int:
        """Возвращает количество уроков курса."""
        return obj.lessons.count()

    def get_is_subscribed(self, obj: Course) -> bool:
        """Возвращает признак подписки текущего пользователя на курс."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return CourseSubscription.objects.filter(user=request.user, course=obj).exists()
