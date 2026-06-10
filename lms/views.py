from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.models import Course, CourseSubscription, Lesson
from lms.paginators import LMSPagination
from lms.permissions import IsOwnerOrModerator, is_moderator
from lms.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курса через ViewSet."""

    serializer_class = CourseSerializer
    pagination_class = LMSPagination
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
        if user.is_staff or user.is_superuser:
            return queryset.all()
        if is_moderator(user):
            return queryset.all()
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        """Привязать новый курс к текущему пользователю."""
        user = self.request.user
        if not user.is_staff and not user.is_superuser and is_moderator(user):
            raise PermissionDenied("Модератор не может создавать курсы.")
        serializer.save(owner=user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """Получение списка уроков и создание урока."""

    serializer_class = LessonSerializer
    pagination_class = LMSPagination
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
        if user.is_staff or user.is_superuser:
            return queryset.all()
        if is_moderator(user):
            return queryset.all()
        return queryset.filter(owner=user)

    def perform_create(self, serializer):
        """Привязать новый урок к текущему пользователю."""
        user = self.request.user
        if not user.is_staff and not user.is_superuser and is_moderator(user):
            raise PermissionDenied("Модератор не может создавать уроки.")
        serializer.save(owner=user)


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
        if user.is_staff or user.is_superuser:
            return queryset.all()
        if is_moderator(user):
            return queryset.all()
        return queryset.filter(owner=user)


class CourseSubscriptionAPIView(APIView):
    """Добавление или удаление подписки текущего пользователя на курс."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        course_id = request.data.get("course_id")
        if not course_id:
            return Response(
                {"course_id": "Передайте id курса в поле course_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course_item = get_object_or_404(Course, pk=course_id)
        subs_item = CourseSubscription.objects.filter(
            user=request.user,
            course=course_item,
        )

        if subs_item.exists():
            subs_item.delete()
            message = "подписка удалена"
        else:
            CourseSubscription.objects.create(user=request.user, course=course_item)
            message = "подписка добавлена"

        return Response({"message": message})
