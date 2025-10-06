from django.urls import path
from . import views

urlpatterns = [
    path('notifications/json/', views.notifications_json, name='notifications_json'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
]
