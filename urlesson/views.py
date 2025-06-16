from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import TeacherAvailability
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomUser, LessonRequest
from .forms import LessonRequestForm
from .forms import (
    CustomUserCreationForm,
    CustomUserExtraForm,
    EmailAuthenticationForm,
    LessonRequestForm,
    TeacherAvailabilityForm,
    TeacherPricingForm,
)

def home(request):
    return render(request, 'home.html')

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
    if role is None:
        if request.user.is_authenticated:
            if request.user.role == 'student':
                role = 'teacher'
            elif request.user.role == 'teacher':
                role = 'student'
            else:
                role = 'student'
        else:
            role = 'student'

    users = CustomUser.objects.all()
    if request.user.is_authenticated:
        users = users.exclude(id=request.user.id)
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
def teacher_availability_view(request):
    if request.method == 'POST':
        form = TeacherAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.teacher = request.user
            availability.save()
            return redirect('teacher_availability')
    else:
        form = TeacherAvailabilityForm()

    availabilities = TeacherAvailability.objects.filter(teacher=request.user)
    return render(request, 'availability.html', {
        'form': form,
        'availabilities': availabilities
    })

@login_required
def book_lesson_view(request, teacher_id):
    teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
    if request.method == 'POST':
        form = LessonRequestForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.student = request.user
            lesson.teacher = teacher

            try:
                selected_date_str = request.POST.get('selected_date')
                selected_time_str = request.POST.get('selected_time')
                lesson.date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
                lesson.time = datetime.strptime(selected_time_str, "%H:%M").time()
            except (TypeError, ValueError):
                form.add_error(None, "Invalid date or time format.")
                return render(request, 'book_lesson.html', {
                    'form': form,
                    'teacher': teacher
                })

            #is teacher available?
            if not is_slot_available(teacher, lesson.date, lesson.time, lesson.duration_minutes):
                messages.error(request, "Selected time is unavailable. Please choose a green time slot.")
                return render(request, 'book_lesson.html', {
                    'form': form,
                    'teacher': teacher
                })

            lesson.is_one_time = lesson.repeat_weeks <= 1
            lesson.save()

            #is lessons cyclic?
            if lesson.repeat_weeks > 1:
                for i in range(1, lesson.repeat_weeks):
                    LessonRequest.objects.create(
                        student=lesson.student,
                        teacher=lesson.teacher,
                        date=lesson.date + timedelta(weeks=i),
                        time=lesson.time,
                        duration_minutes=lesson.duration_minutes,
                        is_group=lesson.is_group,
                        repeat_weeks=1,
                        is_one_time=False,
                        status='pending'
                    )
            messages.success(request, "Lesson successfully booked.")
            return redirect('calendar')
        else:
            print("Form errors:", form.errors)

    else:
        form = LessonRequestForm()

    return render(request, 'book_lesson.html', {
        'form': form,
        'teacher': teacher
    })



@login_required
def lesson_calendar_json(request):
    teacher_id = request.GET.get('teacher_id')

    if teacher_id:
        teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
        lessons = LessonRequest.objects.filter(teacher=teacher)
        availabilities = TeacherAvailability.objects.filter(teacher=teacher)
    else:
        user = request.user
        if user.role == 'teacher':
            lessons = LessonRequest.objects.filter(teacher=user)
            availabilities = TeacherAvailability.objects.filter(teacher=user)
        else:
            lessons = LessonRequest.objects.filter(student=user)
            availabilities = [] #student don't have availability
    events = []

    for lesson in lessons:
        start_time = f"{lesson.date}T{lesson.time}"
        end_hour = lesson.time.hour + lesson.duration_minutes // 60
        end_min = lesson.time.minute + lesson.duration_minutes % 60
        if end_min >= 60:
            end_hour += 1
            end_min -= 60
        end_time = f"{lesson.date}T{end_hour:02}:{end_min:02}"
        events.append({
            'title': f"Lesson",
            'start': start_time,
            'end': end_time,
            'color': '#dc3545',
        })

    today = datetime.today()
    day_map = {
                'mon': 0,
                'tue': 1,
                'wed': 2,
                'thu': 3,
                'fri': 4,
                'sat': 5,
                'sun': 6,
            }
    for i in range(0, 366):
        current_day = today + timedelta(days=i)
        dow = current_day.weekday()
        for avail in availabilities:
            if day_map[avail.day] == dow:
                start_dt = datetime.combine(current_day.date(), avail.start_time)
                end_dt = datetime.combine(current_day.date(), avail.end_time)
                events.append({
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'display': 'background',
                    'color': '#28a745'
                })

    return JsonResponse(events, safe=False)


@login_required
def calendar_view(request):
    teacher_id = request.GET.get("teacher_id")

    if teacher_id:
        teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
    elif request.user.role == 'teacher':
        teacher = request.user
    else:
        teacher = None

    return render(request, 'calendar.html', {
        'teacher': teacher
    })



from django.utils.timezone import datetime, timedelta

from datetime import datetime, timedelta

@login_required
def teacher_availability_json(request):
    teacher_id = request.GET.get("teacher_id")
    if not teacher_id:
        teacher_id = request.user.id

    availabilities = TeacherAvailability.objects.filter(teacher_id=teacher_id)

    today = datetime.today()
    events = []

    for i in range(7):
        current_date = today + timedelta(days=i)
        weekday = current_date.weekday()
        for a in availabilities:
            if a.day == weekday:
                start_dt = datetime.combine(current_date.date(), a.start_time)
                end_dt = datetime.combine(current_date.date(), a.end_time)
                events.append({
                    'title': 'Available',
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'color': '#28a745',
                    'display': 'background',
                })

    return JsonResponse(events, safe=False)

def is_slot_available(teacher, date, time, duration_minutes):
    day_map = {
        0: 'mon', 1: 'tue', 2: 'wed',
        3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'
    }
    weekday = date.weekday()
    day_name = day_map[weekday]
    
    # teacher availability 
    availabilities = TeacherAvailability.objects.filter(teacher=teacher, day=day_name)
    if not availabilities.exists():
        return False
    
    lesson_start = datetime.combine(date, time)
    lesson_end = lesson_start + timedelta(minutes=duration_minutes)
    
    for availability in availabilities:
        availability_start = datetime.combine(date, availability.start_time)
        availability_end = datetime.combine(date, availability.end_time)
        
        # teacher have availability?
        if lesson_start >= availability_start and lesson_end <= availability_end:
            # colisions with another lessons
            conflicting_lessons = LessonRequest.objects.filter(
                teacher=teacher,
                date=date,
                status__in=['pending', 'accepted']
            ).exclude(status='rejected')
            
            for lesson in conflicting_lessons:
                lesson_start_time = datetime.combine(date, lesson.time)
                lesson_end_time = lesson_start_time + timedelta(minutes=lesson.duration_minutes)
                
                if (lesson_start < lesson_end_time and lesson_end > lesson_start_time):
                    return False
            
            return True
    
    return False


def lesson_success(request):
    return render(request, 'lesson_success.html')