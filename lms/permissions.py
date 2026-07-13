from rest_framework.permissions import SAFE_METHODS, BasePermission

MODERATOR_GROUP_NAME = "Модераторы"


def is_moderator(user) -> bool:
    """Возвращает True, если пользователь принадлежит к группе модераторов."""
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name=MODERATOR_GROUP_NAME).exists()
    )


class IsOwnerOrModerator(BasePermission):
    """Правила доступа к курсам и урокам.

    Обычные пользователи могут просматривать, редактировать и удалять только собственные объекты.
    Модераторы могут просматривать и редактировать любые объекты, но не могут создавать или удалять их.
    Сотрудникам и суперпользователям разрешено выполнять любые действия.
    """

    def has_permission(self, request, view) -> bool:
        """Проверка разрешения уровня запроса."""
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.is_superuser:
            return True

        if is_moderator(user):
            return request.method in (*SAFE_METHODS, "PUT", "PATCH")

        return True

    def has_object_permission(self, request, view, obj) -> bool:
        """Проверка разрешения на уровне объектов."""
        user = request.user
        if user.is_staff or user.is_superuser:
            return True

        if is_moderator(user):
            return request.method in (*SAFE_METHODS, "PUT", "PATCH")

        return getattr(obj, "owner_id", None) == user.id
