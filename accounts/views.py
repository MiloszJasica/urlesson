from django.shortcuts import render

# Create your views here.
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomUserCreationForm, EmailAuthenticationForm
from .models import CustomUser, Teacher, Student
from .forms import TeacherExtraForm, StudentExtraForm

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
            return redirect('profile')
    else:
        form = ExtraFormClass()

    return render(request, 'accounts/register_extra.html', {'form': form})
