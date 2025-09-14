from django.urls import path, include
from . import views
from django.contrib.auth.views import LogoutView
from .views import edit_pricing_view
from .views import book_lesson_view
from django.contrib.auth import views as auth_views
from accounts.views import profile_view

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('users/', views.teacher_list_view, name='teacher_list'),
    path("profile/", profile_view, name="profile"),
    path('teacher/pricing/', views.edit_pricing_view, name='teacher_pricing'),
    path('teacher/availability/', views.teacher_availability_view, name='teacher_availability'),
    path('teacher/<int:teacher_id>/book/', views.book_lesson_view, name='book_lesson'),
    path('lesson_calendar_json/', views.lesson_calendar_json, name='lesson_calendar_json'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/availability-json/', views.teacher_availability_json, name='teacher_availability_json'),
]