from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserExtraForm, EmailAuthenticationForm


def home(request):
    return render(request, 'base.html')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('register_extra')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required
def register_extra_view(request):
    user = request.user
    if request.method == 'POST':
        form = CustomUserExtraForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CustomUserExtraForm(instance=user)
    return render(request, 'register_extra.html', {'form': form})


@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})

#@login_required
def user_list_view(request, role):
    users = CustomUser.objects.filter(role=role)
    fields = ['email', 'first_name', 'last_name']
    return render(request, 'user_list.html', {
        'object_list': users,
        'field_names': fields,
        'role': role
    })





def password_change(request):
    return HttpResponse("Strona password_change jeszcze nie gotowa")


def password_change_done(request):
    return HttpResponse("Strona password_change_done jeszcze nie gotowa")


class CustomLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = 'login.html'