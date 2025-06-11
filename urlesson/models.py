from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from decimal import Decimal

class CustomUser(AbstractUser):
    username = None
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    can_commute = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    price_per_minute_individual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_per_minute_group = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    extra_student_group_minute_price = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    recurring_discount_percent = models.PositiveIntegerField(default=0, help_text="Discount % for recurring lessons")

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'


class LessonRequest(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_requests'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teaching_requests'
    )

    DURATION_CHOICES = [
        (30, '30 minutes'),
        (35, '35 minutes'),
        (40, '40 minutes'),
        (45, '45 minutes'),
        (55, '55 minutes'),
        (60, '60 minutes'),
        (75, '75 minutes'),
        (90, '90 minutes'),
        (120, '120 minutes'),
    ]

    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(choices=DURATION_CHOICES, default=60)
    is_one_time = models.BooleanField(default=True)
    is_group = models.BooleanField(default=False)

    repeat_weeks = models.PositiveIntegerField(default=1, help_text="Number of weekly lessons (1 = one-time)")

    final_price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.teacher.price_per_minute_individual:
            price = self.teacher.price_per_minute_individual * Decimal(self.duration_minutes)

            if self.is_group:
                try:
                    num_students = self.invited_students.count() + 1 
                except AttributeError:
                    num_students = 2

                price = self.teacher.price_per_minute_group * Decimal(self.duration_minutes)
                if num_students > 2:
                    price += self.teacher.extra_student_group_minute_price * Decimal(self.duration_minutes) * (num_students - 2)

            self.final_price = price

        super().save(*args, **kwargs)

class TeacherAvailability(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='availabilities')
    day = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('teacher', 'day')
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.get_day_display()}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
