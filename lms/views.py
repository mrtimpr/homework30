from rest_framework import generics, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from lms.models import Course, Lesson
from lms.permissions import IsOwnerOrModerator, is_moderator
from lms.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курса через ViewSet."""

    serializer_class = CourseSerializer
    permission_classes_by_action = {
        "list": [IsAuthenticated, IsOwnerOrModerator],
        "retrieve": [IsAuthenticated, IsOwnerOrModerator],
        "create": [IsAuthenticated, IsOwnerOrModerator],
        "update": [IsAuthenticated, IsOwnerOrModerator],
        "partial_update": [IsAuthenticated, IsOwnerOrModerator],
        "destroy": [IsAuthenticated, IsOwnerOrModerator],
    }

    def get_permissions(self):
        """Возвращать явные классы разрешений для каждого действия ViewSet."""
        permission_classes = self.permission_classes_by_action.get(
            self.action,
            [IsAuthenticated, IsOwnerOrModerator],
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Модераторы и сотрудники видят все курсы, обычные пользователи — только свои."""
        queryset = Course.objects.prefetch_related("lessons").select_related("owner")
        user = self.request.user
        if user.is_staff or user.is_superuser or is_moderator(user):
            return queryset.all()
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        """Привязать новый курс к текущему пользователю."""
        if is_moderator(self.request.user) and not self.request.user.is_staff:
            raise PermissionDenied("Модератор не может создавать курсы.")
        serializer.save(owner=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """Получение списка уроков и создание урока."""

    serializer_class = LessonSerializer
    permission_classes_by_method = {
        "GET": [IsAuthenticated, IsOwnerOrModerator],
        "POST": [IsAuthenticated, IsOwnerOrModerator],
    }

    def get_permissions(self):
        """Возвращать явные классы разрешений для действий списка и создания."""
        permission_classes = self.permission_classes_by_method.get(
            self.request.method,
            [IsAuthenticated, IsOwnerOrModerator],
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Модераторы и сотрудники видят все уроки, обычные пользователи — только свои."""
        queryset = Lesson.objects.select_related("course", "owner")
        user = self.request.user
        if user.is_staff or user.is_superuser or is_moderator(user):
            return queryset.all()
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        """Привязать новый урок к текущему пользователю."""
        if is_moderator(self.request.user) and not self.request.user.is_staff:
            raise PermissionDenied("Модератор не может создавать уроки.")
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Получение, изменение и удаление одного урока."""

    serializer_class = LessonSerializer
    permission_classes_by_method = {
        "GET": [IsAuthenticated, IsOwnerOrModerator],
        "PUT": [IsAuthenticated, IsOwnerOrModerator],
        "PATCH": [IsAuthenticated, IsOwnerOrModerator],
        "DELETE": [IsAuthenticated, IsOwnerOrModerator],
    }

    def get_permissions(self):
        """Возвращать явные классы разрешений для действий детализации."""
        permission_classes = self.permission_classes_by_method.get(
            self.request.method,
            [IsAuthenticated, IsOwnerOrModerator],
        )
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Модераторы и сотрудники видят все уроки, обычные пользователи — только свои."""
        queryset = Lesson.objects.select_related("course", "owner")
        user = self.request.user
        if user.is_staff or user.is_superuser or is_moderator(user):
            return queryset.all()
        return queryset.filter(owner=user)