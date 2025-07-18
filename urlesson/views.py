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
from .models import Teacher, Student
from django.utils.timezone import datetime, timedelta
from datetime import datetime, timedelta
from .forms import (
    CustomUserCreationForm,
    EmailAuthenticationForm,
    LessonRequestForm,
    TeacherAvailabilityForm,
    TeacherPricingForm,
    TeacherExtraForm, StudentExtraForm
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
            user = form.save(commit=False)
            user.save() 
            login(request, user)
            
            request.session['user_id'] = user.id
            request.session['role'] = user.role
            
            return redirect('register_extra')
        else:
            print("Form errors:", form.errors)
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})


def register_extra_view(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')

    if not user_id or not role:
        return redirect('register')

    user = get_object_or_404(CustomUser, id=user_id)

    if role == 'teacher':
        ExtraFormClass = TeacherExtraForm
        profile_model = Teacher
    else:
        ExtraFormClass = StudentExtraForm
        profile_model = Student

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



def teacher_list_view(request):
    users = CustomUser.objects.filter(role='teacher').select_related('teacher_profile')

    if request.user.is_authenticated:
        users = users.exclude(id=request.user.id)

    return render(request, 'teacher_list.html', {
        'object_list': users,
    })


@login_required
def my_schedule_view(request):
    user = request.user
    if user.is_teacher():
        lessons = LessonRequest.objects.filter(teacher=user.teacher_profile, status='accepted')
    else:
        lessons = LessonRequest.objects.filter(student=user.student_profile, status='accepted')
    return render(request, 'my_schedule.html', {'lessons': lessons})


@login_required
def edit_pricing_view(request):
    if not request.user.is_teacher():
        messages.error(request, "You are not a teacher.")
        return redirect('profile')

    teacher_profile = get_object_or_404(Teacher, user=request.user)

    if request.method == 'POST':
        form = TeacherPricingForm(request.POST, instance=teacher_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Prices updated successfully.")
            return redirect('profile')
    else:
        form = TeacherPricingForm(instance=teacher_profile)

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
    teacher_profile = get_object_or_404(Teacher, user=teacher)
    subject_list = teacher_profile.subjects.all()

    if request.method == 'POST':
        form = LessonRequestForm(request.POST, teacher=teacher)

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
                    'teacher': teacher,
                    'subject_list': subject_list,
                })

            # przypisz subject po ID
            subject_id = request.POST.get("subject")
            if subject_id:
                try:
                    subject = subject_list.get(id=subject_id)
                    lesson.subject = subject
                except Subject.DoesNotExist:
                    form.add_error(None, "Invalid subject.")
                    return render(request, 'book_lesson.html', {
                        'form': form,
                        'teacher': teacher,
                        'subject_list': subject_list,
                    })

            if not is_slot_available(teacher, lesson.date, lesson.time, lesson.duration_minutes):
                messages.error(request, "Selected time is unavailable. Please choose a green time slot.")
                return render(request, 'book_lesson.html', {
                    'form': form,
                    'teacher': teacher,
                    'subject_list': subject_list,
                })

            lesson.is_one_time = lesson.repeat_weeks <= 1
            lesson.save()

            if lesson.repeat_weeks > 1:
                for i in range(1, lesson.repeat_weeks):
                    LessonRequest.objects.create(
                        student=lesson.student,
                        teacher=lesson.teacher,
                        subject=lesson.subject,
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
        form = LessonRequestForm(teacher=teacher)

    return render(request, 'book_lesson.html', {
        'form': form,
        'teacher': teacher,
        'subject_list': subject_list,
        'price_individual': getattr(teacher.teacher_profile, 'price_per_minute_individual', 0),
    })




@login_required
def lesson_calendar_json(request):
    teacher_id = request.GET.get('teacher_id')
    subject_list = []

    if teacher_id:
        teacher_user = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
        teacher = get_object_or_404(Teacher, user=teacher_user)
        lessons = LessonRequest.objects.filter(teacher=teacher_user)

        availabilities = TeacherAvailability.objects.filter(teacher=teacher_user)

        subject_list = [{'id': sub.id, 'name': sub.name} for sub in teacher.subjects.all()]
    else:
        user = request.user
        if user.role == 'teacher':
            teacher = get_object_or_404(Teacher, user=user)
            lessons = LessonRequest.objects.filter(teacher=user)
            availabilities = TeacherAvailability.objects.filter(teacher=user)
            subject_list = [{'id': sub.id, 'name': sub.name} for sub in teacher.subjects.all()]
        else:
            lessons = LessonRequest.objects.filter(student=user)
            availabilities = []
            subject_list = []

    events = []

    for lesson in lessons:
        start_time = f"{lesson.date}T{lesson.time}"
        end_hour = lesson.time.hour + lesson.duration_minutes // 60
        end_min = lesson.time.minute + lesson.duration_minutes % 60
        if end_min >= 60:
            end_hour += 1
            end_min -= 60
        end_time = f"{lesson.date}T{end_hour:02}:{end_min:02}"

        if request.user.role == 'student':
            other_person = lesson.teacher
        else:
            other_person = lesson.student

        full_name = f"{other_person.first_name} {other_person.last_name}".strip()
        if not full_name.strip():
            full_name = "No Name"

        subject_name = lesson.subject.name if getattr(lesson, 'subject', None) else 'Lesson'
        title = f"{subject_name} with {full_name}"

        events.append({
            'title': title,
            'start': start_time,
            'end': end_time,
            'color': '#dc3545',
        })


    today = datetime.today()
    day_map = {
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
        'fri': 4, 'sat': 5, 'sun': 6,
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