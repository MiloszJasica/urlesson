from django.urls import path
from . import views
from .views import CustomLoginView
from django.contrib.auth.views import LogoutView
from .views import edit_pricing_view
from .views import book_lesson_view

urlpatterns = [
    path('', views.home, name='home'), 
    path('register/', views.register_view, name='register'),
    path('register/extra/', views.register_extra_view, name='register_extra'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.user_list_view, name='user_list'),
    path('teacher/pricing/', edit_pricing_view, name='teacher_pricing'),
    path('password_change/', views.password_change, name='password_change'),
    path('password_change/done/', views.password_change_done, name='password_change_done'),
    path('teacher/<int:teacher_id>/book/', book_lesson_view, name='book_lesson'),



]