from django.contrib.auth.models import AbstractUser
from django.db import models

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
    
    

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'
