from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from decimal import Decimal
from accounts.models import CustomUser, Teacher, Student, Subject

from django.contrib.auth.base_user import BaseUserManager

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
        (60, '60 minutes'),
        (90, '90 minutes'),
        (120, '120 minutes'),
    ]
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_requests'
    )
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

    from decimal import Decimal

    def save(self, *args, **kwargs):
        teacher_profile = getattr(self.teacher, 'teacher_profile', None)
        if teacher_profile and teacher_profile.price_per_minute_individual:
            if self.is_group:
                try:
                    num_students = self.invited_students.count() + 1
                except AttributeError:
                    num_students = 2

                price = teacher_profile.price_per_minute_group * Decimal(self.duration_minutes)

                if num_students > 2:
                    price += (
                        teacher_profile.extra_student_group_minute_price *
                        Decimal(self.duration_minutes) *
                        (num_students - 2)
                    )
            else:
                price = teacher_profile.price_per_minute_individual * Decimal(self.duration_minutes)

            self.final_price = price
        else:
            self.final_price = Decimal(0)

        super().save(*args, **kwargs)

class TeacherDayOff(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="days_off")
    date = models.DateField()

    class Meta:
        unique_together = ('teacher', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.teacher} - day off {self.date}"

class TeacherAvailabilityPeriod(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="availability_periods")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    def __str__(self):
        return f"{self.teacher.email} | {self.start_datetime} - {self.end_datetime}"
