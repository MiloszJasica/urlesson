from django.shortcuts import render

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomUserCreationForm, EmailAuthenticationForm
from .models import CustomUser, Teacher, Student
from .forms import TeacherExtraForm, StudentExtraForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm

#ACCOUNT CREATION AND LOGIN VIEWS

class CustomLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        messages.success(self.request, "Logged In.")
        return super().form_valid(form)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            request.session['user_id'] = user.id
            request.session['role'] = user.role
            return redirect('accounts:register_extra')
        else:
            print("Form errors:", form.errors)
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def register_extra_view(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')

    if not user_id or not role:
        return redirect('accounts:register')

    user = get_object_or_404(CustomUser, id=user_id)

    ExtraFormClass = TeacherExtraForm if role == 'teacher' else StudentExtraForm
    profile_model = Teacher if role == 'teacher' else Student

    if request.method == 'POST':
        form = ExtraFormClass(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = user
            profile.save()
            del request.session['user_id']
            del request.session['role']
            return redirect('accounts:profile')
    else:
        form = ExtraFormClass()

    return render(request, 'accounts/register_extra.html', {'form': form})

#PROFILE AND SCHEDULE VIEWS

@login_required
def profile_view(request):
    user = request.user
    password_form = SetPasswordForm(request.user)
    show_password_form = False 

    editable_fields = [
        ('Email', 'email'),
        ('Role', 'get_role_display'),
        ('Date of birth', 'date_of_birth'),
        ('On-site visit', 'can_commute'),
        ('City', 'city'),
        ('Password', 'password'),
    ]

    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')

        if field == 'password':
            show_password_form = True 
            form = SetPasswordForm(request.user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password changed successfully.")
                return redirect('accounts:profile')
            else:
                password_form = form

        elif field in ['email', 'first_name', 'last_name', 'date_of_birth', 'can_commute', 'city']:
            setattr(user, field, value)
            user.save()
            messages.success(request, f'Changed field: {field}')
            return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
        'editable_fields': editable_fields,
        'password_form': password_form,
        'show_password_form': show_password_form,
    })
