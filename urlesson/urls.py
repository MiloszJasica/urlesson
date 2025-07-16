from django.urls import path
from . import views
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView
from .views import edit_pricing_view
from .views import book_lesson_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('register/extra/', views.register_extra_view, name='register_extra'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.teacher_list_view, name='teacher_list'),

    path('teacher/pricing/', views.edit_pricing_view, name='teacher_pricing'),
    path('teacher/availability/', views.teacher_availability_view, name='teacher_availability'),
    path('teacher/<int:teacher_id>/book/', views.book_lesson_view, name='book_lesson'),
    path('my_schedule/', views.my_schedule_view, name='my_schedule'),
    path('lesson_calendar_json/', views.lesson_calendar_json, name='lesson_calendar_json'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/availability-json/', views.teacher_availability_json, name='teacher_availability_json'),


]