from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import PaymentViewSet, UserRegisterAPIView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("register/", UserRegisterAPIView.as_view(), name="register"),
    path("", include(router.urls)),
]