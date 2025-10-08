from django.contrib import admin
from .models import LessonRequest, TeacherAvailabilityPeriod
from accounts.models import CustomUser, Teacher, Student, Subject

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role','first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'price_per_minute_individual', 'price_per_minute_group', 'recurring_discount_percent')
    search_fields = ('user__email',)
    filter_horizontal = ('subjects',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'school', 'number_class')
    search_fields = ('user__email',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(LessonRequest)
class LessonRequestAdmin(admin.ModelAdmin):
    list_display = ('student_email', 'teacher_email', 'date', 'time', 'duration_minutes', 'status', 'final_price')
    list_filter = ('status',)
    search_fields = ('student__email', 'teacher__email')

    def student_email(self, obj):
        return obj.student.email
    student_email.short_description = 'Student Email'

    def teacher_email(self, obj):
        return obj.teacher.email
    teacher_email.short_description = 'Teacher Email'

@admin.register(TeacherAvailabilityPeriod)
class TeacherAvailabilityPeriodAdmin(admin.ModelAdmin):
    list_display = ('teacher_email', 'start_datetime', 'end_datetime')
    search_fields = ('teacher__email',)

    def teacher_email(self, obj):
        return obj.teacher.email
    teacher_email.short_description = 'Teacher Email'
    
