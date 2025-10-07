from django.urls import path, include
from . import views
from accounts.views import edit_pricing_view
from accounts.views import profile_view
from .views import student_calendar_view, student_calendar_json


urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('notifications/', include('notifications.urls')),
    path('users/', views.teacher_list_view, name='teacher_list'),
    path("profile/", profile_view, name="profile"),
    path('teacher/pricing/', edit_pricing_view, name='teacher_pricing'),
    path('teacher/availability/', views.teacher_availability_view, name='teacher_availability'),
    path('teacher/<int:teacher_id>/book/', views.book_lesson_view, name='book_lesson'),
    path('lesson_calendar_json/', views.lesson_calendar_json, name='lesson_calendar_json'),
    path("student/calendar/json/", student_calendar_json, name="student_calendar_json"),
    path("student/calendar/", student_calendar_view, name="student_calendar"),
    path('calendar/availability-json/', views.teacher_availability_json, name='teacher_availability_json'),
    path('confirm-lessons/<int:teacher_id>/', views.confirm_lessons_view, name='confirm_lessons'),
    path('add-availability/', views.add_availability, name='add_availability'),
    path('delete-availability/', views.delete_availability, name='delete_availability'),
    path('update-lesson-status/', views.update_lesson_status, name='update_lesson_status'),
]