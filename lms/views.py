from rest_framework import generics, viewsets

from lms.models import Course, Lesson
from lms.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD для курса через ViewSet."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """Получение списка уроков и создание урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Получение, изменение и удаление одного урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer