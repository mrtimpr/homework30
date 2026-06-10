from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsSelfForWriteOrReadOnly(BasePermission):
    """Разрешить любому аутентифицированному пользователю просматривать профили, но редактировать только свой собственный."""

    def has_permission(self, request, view) -> bool:
        """Требовать аутентификацию для защищенных пользовательских эндпоинтов."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        """Разрешить чтение всем аутентифицированным пользователям, а запись — только владельцу и администратору."""
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff or request.user.is_superuser


class IsOwnerPaymentOrStaff(BasePermission):
    """Разрешить пользователям работать только со своими платежами, если они не являются сотрудниками."""

    def has_permission(self, request, view) -> bool:
        """Требовать аутентификацию для конечных точек оплаты."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        """Предоставить доступ владельцу платежа или сотрудникам."""
        return obj.user_id == request.user.id or request.user.is_staff or request.user.is_superuser
