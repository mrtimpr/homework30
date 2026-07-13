from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, CourseSubscription, Lesson
from lms.permissions import MODERATOR_GROUP_NAME


User = get_user_model()


class LMSAPITestCase(APITestCase):
    """Тесты для курсов, уроков, валидаторов, пагинации и подписок."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            first_name="Owner",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
        )
        self.moderator = User.objects.create_user(
            email="moderator@example.com",
            password="testpass123",
            first_name="Moderator",
        )
        self.moderator_group = Group.objects.create(name=MODERATOR_GROUP_NAME)
        self.moderator.groups.add(self.moderator_group)

        self.course = Course.objects.create(
            owner=self.user,
            name="Python course",
            description="Base course",
        )
        self.other_course = Course.objects.create(
            owner=self.other_user,
            name="Other course",
            description="Hidden course",
        )
        self.lesson = Lesson.objects.create(
            owner=self.user,
            course=self.course,
            name="Lesson 1",
            description="Intro",
            video_url="https://www.youtube.com/watch?v=abc123",
        )

    def test_course_list_is_paginated_and_contains_subscription_flag(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("courses-list")

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("is_subscribed", response.data["results"][0])

    def test_lesson_list_is_paginated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("lesson-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)

    def test_course_crud_owner(self):
        self.client.force_authenticate(user=self.user)
        list_url = reverse("courses-list")

        create_response = self.client.post(
            list_url,
            {"name": "Django course", "description": "DRF"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["owner"], self.user.id)

        detail_url = reverse("courses-detail", kwargs={"pk": create_response.data["id"]})
        retrieve_response = self.client.get(detail_url)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)

        patch_response = self.client.patch(
            detail_url,
            {"name": "Updated Django course"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["name"], "Updated Django course")

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_user_cannot_access_foreign_course(self):
        self.client.force_authenticate(user=self.other_user)
        detail_url = reverse("courses-detail", kwargs={"pk": self.course.pk})

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_lesson_crud_owner_and_youtube_validator(self):
        self.client.force_authenticate(user=self.user)
        list_url = reverse("lesson-list-create")

        invalid_response = self.client.post(
            list_url,
            {
                "course": self.course.pk,
                "name": "Bad video",
                "description": "Invalid link",
                "video_url": "https://example.com/video",
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

        create_response = self.client.post(
            list_url,
            {
                "course": self.course.pk,
                "name": "Good video",
                "description": "Valid link",
                "video_url": "https://youtube.com/watch?v=good",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["owner"], self.user.id)

        detail_url = reverse("lesson-detail", kwargs={"pk": create_response.data["id"]})
        retrieve_response = self.client.get(detail_url)
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)

        patch_response = self.client.patch(
            detail_url,
            {"name": "Updated lesson"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["name"], "Updated lesson")

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_create_lesson_in_foreign_course(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("lesson-list-create")

        response = self.client.post(
            url,
            {
                "course": self.course.pk,
                "name": "Foreign course lesson",
                "description": "Forbidden",
                "video_url": "https://youtube.com/watch?v=abc",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_moderator_can_update_but_cannot_create_or_delete_course_and_lesson(self):
        self.client.force_authenticate(user=self.moderator)

        course_create_response = self.client.post(
            reverse("courses-list"),
            {"name": "Moderator course"},
            format="json",
        )
        self.assertEqual(course_create_response.status_code, status.HTTP_403_FORBIDDEN)

        course_detail_url = reverse("courses-detail", kwargs={"pk": self.course.pk})
        course_patch_response = self.client.patch(
            course_detail_url,
            {"description": "Changed by moderator"},
            format="json",
        )
        self.assertEqual(course_patch_response.status_code, status.HTTP_200_OK)

        course_delete_response = self.client.delete(course_detail_url)
        self.assertEqual(course_delete_response.status_code, status.HTTP_403_FORBIDDEN)

        lesson_create_response = self.client.post(
            reverse("lesson-list-create"),
            {
                "course": self.course.pk,
                "name": "Moderator lesson",
                "video_url": "https://youtube.com/watch?v=mod",
            },
            format="json",
        )
        self.assertEqual(lesson_create_response.status_code, status.HTTP_403_FORBIDDEN)

        lesson_detail_url = reverse("lesson-detail", kwargs={"pk": self.lesson.pk})
        lesson_patch_response = self.client.patch(
            lesson_detail_url,
            {"description": "Changed by moderator"},
            format="json",
        )
        self.assertEqual(lesson_patch_response.status_code, status.HTTP_200_OK)

        lesson_delete_response = self.client.delete(lesson_detail_url)
        self.assertEqual(lesson_delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_subscription_toggle_and_course_subscription_flag(self):
        self.client.force_authenticate(user=self.user)
        subscription_url = reverse("course-subscription")

        add_response = self.client.post(
            subscription_url,
            {"course_id": self.course.pk},
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_200_OK)
        self.assertEqual(add_response.data["message"], "подписка добавлена")
        self.assertTrue(
            CourseSubscription.objects.filter(user=self.user, course=self.course).exists()
        )

        course_response = self.client.get(
            reverse("courses-detail", kwargs={"pk": self.course.pk})
        )
        self.assertEqual(course_response.status_code, status.HTTP_200_OK)
        self.assertTrue(course_response.data["is_subscribed"])

        delete_response = self.client.post(
            subscription_url,
            {"course_id": self.course.pk},
            format="json",
        )
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertEqual(delete_response.data["message"], "подписка удалена")
        self.assertFalse(
            CourseSubscription.objects.filter(user=self.user, course=self.course).exists()
        )

    def test_subscription_requires_course_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("course-subscription"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
