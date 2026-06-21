from dataclasses import dataclass
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson
from users.models import Payment


@dataclass(frozen=True, slots=True)
class FakeCheckoutData:
    product_id: str = "prod_test"
    price_id: str = "price_test"
    session_id: str = "cs_test"
    payment_link: str = "https://checkout.stripe.com/test"
    status: str = Payment.STATUS_OPEN


User = get_user_model()


class UserAndAuthEndpointTests(APITestCase):
    """Тесты для точек доступа к регистрации, JWT, операциям CRUD с пользователями и платежам."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            first_name="User",
            last_name="PrivateLastName",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="HiddenLastName",
        )
        self.course = Course.objects.create(owner=self.user, name="Paid course")
        self.lesson = Lesson.objects.create(
            owner=self.user,
            course=self.course,
            name="Paid lesson",
            video_url="https://youtube.com/watch?v=pay",
        )
        self.payment = Payment.objects.create(
            user=self.user,
            paid_course=self.course,
            paid_lesson=self.lesson,
            amount=1000,
            payment_method=Payment.PAYMENT_METHOD_CASH,
        )

    def test_registration_success_and_duplicate_email_validation(self):
        url = reverse("register")

        response = self.client.post(
            url,
            {
                "email": "new@example.com",
                "password": "testpass123",
                "first_name": "New",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

        duplicate_response = self.client.post(
            url,
            {
                "email": "new@example.com",
                "password": "testpass123",
                "first_name": "Duplicate",
            },
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_obtain_pair_and_refresh_endpoints(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": "user@example.com", "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_user_endpoints_require_authentication(self):
        response = self.client.get(reverse("users-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_view_any_profile_but_edit_only_own_profile(self):
        self.client.force_authenticate(user=self.user)

        own_response = self.client.get(reverse("users-detail", kwargs={"pk": self.user.pk}))
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertIn("last_name", own_response.data)
        self.assertIn("payments", own_response.data)
        self.assertNotIn("password", own_response.data)

        foreign_response = self.client.get(
            reverse("users-detail", kwargs={"pk": self.other_user.pk})
        )
        self.assertEqual(foreign_response.status_code, status.HTTP_200_OK)
        self.assertNotIn("last_name", foreign_response.data)
        self.assertNotIn("payments", foreign_response.data)
        self.assertNotIn("password", foreign_response.data)

        own_patch_response = self.client.patch(
            reverse("users-detail", kwargs={"pk": self.user.pk}),
            {"first_name": "Updated"},
            format="json",
        )
        self.assertEqual(own_patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_patch_response.data["first_name"], "Updated")

        foreign_patch_response = self.client.patch(
            reverse("users-detail", kwargs={"pk": self.other_user.pk}),
            {"first_name": "Hacked"},
            format="json",
        )
        self.assertEqual(foreign_patch_response.status_code, status.HTTP_403_FORBIDDEN)


    def test_user_can_delete_own_profile(self):
        user_to_delete = User.objects.create_user(
            email="delete-me@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=user_to_delete)

        response = self.client.delete(
            reverse("users-detail", kwargs={"pk": user_to_delete.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=user_to_delete.pk).exists())

    def test_payment_crud_available_for_owner(self):
        self.client.force_authenticate(user=self.user)

        list_response = self.client.get(reverse("payments-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

        create_response = self.client.post(
            reverse("payments-list"),
            {
                "paid_course": self.course.pk,
                "paid_lesson": self.lesson.pk,
                "amount": 1500,
                "payment_method": Payment.PAYMENT_METHOD_TRANSFER,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["user"], self.user.pk)

        detail_url = reverse("payments-detail", kwargs={"pk": create_response.data["id"]})
        patch_response = self.client.patch(
            detail_url,
            {"amount": 2000},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)


    def test_api_documentation_endpoints_available(self):
        url_names = ["schema", "swagger-ui"]

        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("users.views.create_checkout_for_payment")
    def test_stripe_payment_creation_returns_payment_link(self, mocked_checkout):
        mocked_checkout.return_value = FakeCheckoutData()
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("payments-list"),
            {
                "paid_course": self.course.pk,
                "amount": 2500,
                "payment_method": Payment.PAYMENT_METHOD_STRIPE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["payment_link"], "https://checkout.stripe.com/test")
        self.assertEqual(response.data["stripe_session_id"], "cs_test")
        mocked_checkout.assert_called_once()

    @patch("users.views.sync_payment_status_from_stripe")
    def test_stripe_payment_status_check(self, mocked_sync):
        self.payment.payment_method = Payment.PAYMENT_METHOD_STRIPE
        self.payment.stripe_session_id = "cs_test"
        self.payment.status = Payment.STATUS_OPEN
        self.payment.save()
        mocked_sync.return_value = {"id": "cs_test", "payment_status": "paid"}
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("payments-check-status", kwargs={"pk": self.payment.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_sync.assert_called_once()
