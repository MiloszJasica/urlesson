from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    username = None 
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    can_commute = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['role'] 
    
    lesson_price_45min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    lesson_price_60min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    group_lesson_base_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    group_price_per_additional_student = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

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
        (45, '45 minut'),
        (60, '60 minut'),
    ]

    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(choices=DURATION_CHOICES, default=60)

    is_one_time = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    is_group = models.BooleanField(default=False)

    final_price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.teacher and self.duration_minutes:
            if self.is_group:
                base_price = self.teacher.group_lesson_base_price or 0
                extra_price = self.teacher.group_price_per_additional_student or 0
                num_students = getattr(self, 'students_count', 1) 
                self.final_price = base_price + extra_price * max(0, num_students - 2)
            else:
                if self.duration_minutes == 45:
                    self.final_price = self.teacher.lesson_price_45min
                elif self.duration_minutes == 60:
                    self.final_price = self.teacher.lesson_price_60min
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} {self.time} - {self.student.email} → {self.teacher.email}"


class GroupLessonInvite(models.Model):
    lesson_request = models.ForeignKey(LessonRequest, on_delete=models.CASCADE)
    invited_student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    accepted = models.BooleanField(null=True)  # None if no one response

    def __str__(self):
        return f"{self.invited_student.email} → {self.lesson_request}"

class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    weekday = models.IntegerField(choices=[(i, day) for i, day in enumerate([
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ])])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.teacher.email} - {self.get_weekday_display()} {self.start_time}–{self.end_time}"

class TeacherUnavailableSlot(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.teacher.email} unavailable {self.date} at {self.time}"
