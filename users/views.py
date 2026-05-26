from rest_framework import viewsets

from users.models import User
from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """CRUD для пользователя, включая редактирование профиля."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
