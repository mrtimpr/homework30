from django.core.management.base import BaseCommand
from django.utils import timezone

from lms.models import Course, Lesson
from users.models import Payment, User


class Command(BaseCommand):
    """Создаёт демонстрационные данные для таблицы платежей."""

    help = "Создаёт тестового пользователя, курс, уроки и платежи."

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(
            email="student@example.com",
            defaults={
                "first_name": "Иван",
                "last_name": "Студент",
                "phone": "+79990000000",
                "city": "Москва",
            },
        )
        user.set_password("student12345")
        user.save()

        course, _ = Course.objects.get_or_create(
            name="Python-разработка",
            defaults={"description": "Курс по основам Python и Django."},
        )

        lesson_1, _ = Lesson.objects.get_or_create(
            course=course,
            name="Введение в Python",
            defaults={
                "description": "Первый урок курса.",
                "video_url": "https://www.youtube.com/watch?v=example1",
            },
        )
        lesson_2, _ = Lesson.objects.get_or_create(
            course=course,
            name="Основы Django",
            defaults={
                "description": "Урок по основам Django.",
                "video_url": "https://www.youtube.com/watch?v=example2",
            },
        )

        Payment.objects.get_or_create(
            user=user,
            paid_course=course,
            paid_lesson=None,
            amount=15000,
            payment_method=Payment.PAYMENT_METHOD_TRANSFER,
            defaults={"payment_date": timezone.now()},
        )
        Payment.objects.get_or_create(
            user=user,
            paid_course=None,
            paid_lesson=lesson_1,
            amount=3000,
            payment_method=Payment.PAYMENT_METHOD_CASH,
            defaults={"payment_date": timezone.now()},
        )
        Payment.objects.get_or_create(
            user=user,
            paid_course=None,
            paid_lesson=lesson_2,
            amount=3500,
            payment_method=Payment.PAYMENT_METHOD_TRANSFER,
            defaults={"payment_date": timezone.now()},
        )

        self.stdout.write(self.style.SUCCESS("Демонстрационные платежи созданы."))
