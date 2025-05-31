from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserExtraForm, EmailAuthenticationForm
from .forms import TeacherPricingForm
from django.shortcuts import get_object_or_404
from .forms import LessonRequestForm
from .models import CustomUser, LessonRequest
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import update_session_auth_hash

def home(request):
    return render(request, 'base.html')

class CustomLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, "Logged In.")
        return super().form_valid(form)

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


def register_extra_view(request):
    user = request.user
    if request.method == 'POST':
        form = CustomUserExtraForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Registered.")
            return redirect('profile')
    else:
        form = CustomUserExtraForm(instance=user)
    return render(request, 'register_extra.html', {'form': form})

@login_required
def profile_view(request):
    user = request.user
    password_form = SetPasswordForm(request.user)
    show_password_form = False  # Flaga do pokazania formularza

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
                return redirect('profile')
            else:
                password_form = form

        elif field in ['email', 'first_name', 'last_name', 'date_of_birth', 'can_commute', 'city']:
            setattr(user, field, value)
            user.save()
            messages.success(request, f'Changed field: {field}')
            return redirect('profile')

    return render(request, 'profile.html', {
        'user': user,
        'editable_fields': editable_fields,
        'password_form': password_form,
        'show_password_form': show_password_form,
    })



def user_list_view(request):
    role = request.GET.get('role')
    users = CustomUser.objects.all()
    
    if role:
        users = users.filter(role=role)

    return render(request, 'user_list.html', {
        'object_list': users,
        'role': role,
    })


@login_required
def my_schedule_view(request):
    user = request.user
    if user.is_teacher():
        lessons = LessonRequest.objects.filter(teacher=user, status='accepted')
    else:
        lessons = LessonRequest.objects.filter(student=user, status='accepted')
    
    return render(request, 'my_schedule.html', {'lessons': lessons})

@login_required
def edit_pricing_view(request):
    if not request.user.is_teacher():
        messages.error(request, "You are not a teacher.")
        return redirect('profile')

    if request.method == 'POST':
        form = TeacherPricingForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Prices confirmed.")
            return redirect('profile')
    else:
        form = TeacherPricingForm(instance=request.user)

    return render(request, 'teacher_pricing.html', {'form': form})

@login_required
def book_lesson_view(request, teacher_id):
    teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher')

    if request.method == 'POST':
        form = LessonRequestForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.teacher = teacher
            lesson.save()
            students = form.cleaned_data['students']
            lesson.students.set(students)
            lesson.save()
            messages.success(request, "Sended, students must confirm lesson.")
            return redirect('profile')
    else:
        form = LessonRequestForm(initial={'students': [request.user]})

    return render(request, 'book_lesson.html', {'form': form, 'teacher': teacher})



def password_change(request):
    return HttpResponse("Strona password_change jeszcze nie gotowa")


def password_change_done(request):
    return HttpResponse("Strona password_change_done jeszcze nie gotowa")
