from django.urls import path
from .views import CustomLoginView, register_view, register_extra_view
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='/'),  # next_page ustawia redirect
        name='logout'
    ),
    path('register/', register_view, name='register'),
    path('register/extra/', register_extra_view, name='register_extra'),
]
