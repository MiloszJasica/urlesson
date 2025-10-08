from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    can_commute = models.BooleanField(default=False) #in future
    city = models.CharField(max_length=100, blank=True) #if can commute
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    objects = CustomUserManager()

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'
    
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.ManyToManyField(Subject, blank=True)
    price_per_minute_individual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    price_per_minute_group = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    extra_student_group_minute_price = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    recurring_discount_percent = models.PositiveIntegerField(default=0, help_text="Discount % for recurring lessons")

    def __str__(self):
        return f"{self.user.email} - Teacher"

class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    school = models.CharField(max_length=100, blank=True)
    number_class = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return f"{self.user.email} - Student"