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
from .forms import TeacherAvailabilityForm
from .forms import TeacherPricingForm
from collections import defaultdict

def home(request):
    return render(request, 'home.html')

def teacher_list_view(request):
    users = CustomUser.objects.filter(role='teacher').select_related('teacher_profile')

    if request.user.is_authenticated:
        users = users.exclude(id=request.user.id)

    return render(request, 'teacher_list.html', {
        'object_list': users,
    })

#TEACHER AVAILABILITY
def merge_availabilities(availabilities):
    if not availabilities:
        return []

    sorted_avails = sorted(availabilities, key=lambda a: a.start_time)
    merged = [(sorted_avails[0].start_time, sorted_avails[0].end_time)]

    for a in sorted_avails[1:]:
        last_start, last_end = merged[-1]
        if a.start_time <= last_end:  # overlapping or contiguous
            merged[-1] = (last_start, max(last_end, a.end_time))
        else:
            merged.append((a.start_time, a.end_time))

    return merged

def get_merged_availabilities(teacher):
    day_avails = defaultdict(list)

    # zbieramy dostępności
    for avail in teacher.availabilities.all():
        day_avails[avail.day].append(avail)

    # zbieramy lekcje
    lessons = LessonRequest.objects.filter(
        teacher=teacher,
        status__in=['pending', 'accepted']
    )

    merged = {}
    for day, avails in day_avails.items():
        merged_avail = merge_availabilities(avails)
        available_slots = []

        for start, end in merged_avail:
            slot_start = start
            for lesson in lessons:
                if lesson.date.weekday() != ['mon','tue','wed','thu','fri','sat','sun'].index(day):
                    continue
                lesson_start = lesson.time
                lesson_end = (datetime.combine(datetime.today(), lesson.time) + timedelta(minutes=lesson.duration_minutes)).time()

                if lesson_start < end and lesson_end > slot_start:
                    if slot_start < lesson_start:
                        available_slots.append((slot_start, lesson_start))
                    slot_start = max(slot_start, lesson_end)
            if slot_start < end:
                available_slots.append((slot_start, end))

        merged[day] = available_slots

    return merged

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

    merged_availabilities = get_merged_availabilities(request.user)

    return render(request, 'availability.html', {
        'form': form,
        'merged_availabilities': merged_availabilities,
    })


#BOOK LESSON
def find_alternative_slots(teacher, date, time, duration_minutes, max_weeks=12, max_suggestions=3):
    suggestions = []

    for week in range(max_weeks):
        new_date = date + timedelta(weeks=week)
        if is_slot_available(teacher, new_date, time, duration_minutes):
            suggestions.append(new_date)
            break

    for days in range(1, 7):
        new_date = date + timedelta(days=days)
        if is_slot_available(teacher, new_date, time, duration_minutes):
            suggestions.append(new_date)
            break

    last_lesson = LessonRequest.objects.filter(teacher=teacher).order_by('-date', '-time').first()
    if last_lesson:
        check_date = last_lesson.date + timedelta(days=1)
        for week in range(max_weeks):
            new_date = check_date + timedelta(weeks=week)
            if is_slot_available(teacher, new_date, time, duration_minutes):
                suggestions.append(new_date)
                break

    return suggestions[:max_suggestions]



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
            request.session['pending_lesson'] = {
                'teacher_id': teacher.id,
                'student_id': request.user.id,
                'date': str(lesson.date),
                'time': str(lesson.time),
                'duration_minutes': lesson.duration_minutes,
                'subject_id': lesson.subject.id if lesson.subject else None,
                'repeat_weeks': lesson.repeat_weeks,
            }
            request.session.modified = True

            conflicts = []
            proposals = []

            if lesson.repeat_weeks > 1:
                successful = 1
                failed = 0
                conflicts = []
                proposals = []

                for i in range(1, lesson.repeat_weeks):
                    next_date = lesson.date + timedelta(weeks=i)

                    if is_slot_available(teacher, next_date, lesson.time, lesson.duration_minutes):
                        proposals.append({
                            "date": next_date,
                            "time": lesson.time,
                            "status": "free"
                        })
                        successful += 1
                    else:
                        conflicts.append({
                            "original_date": next_date,
                            "time": lesson.time,
                            "status": "conflict"
                        })
                        failed += 1

                return render(request, 'confirm_lesson.html', {
                    'lesson': lesson,
                    'conflicts': conflicts,
                    'proposals': proposals,
                    'teacher': teacher,
                    'summary': {
                        'successful': successful,
                        'failed': failed,
                        'total': lesson.repeat_weeks,
                    }
                })
            else:
                lesson.status = "pending"
                lesson.save()
                messages.success(request, "Lesson(s) successfully booked!")
                return redirect('calendar')
    else:
        form = LessonRequestForm(teacher=teacher)

    return render(request, 'book_lesson.html', {
        'form': form,
        'teacher': teacher,
        'subject_list': subject_list,
        'price_individual': getattr(teacher.teacher_profile, 'price_per_minute_individual', 0),
    })

from datetime import datetime as dt, time as dt_time, date as dt_date

@login_required
def confirm_lessons_view(request, teacher_id):
    if request.method == "POST":
        pending_lesson = request.session.get('pending_lesson')
        if not pending_lesson:
            messages.error(request, "No pending lesson data found.")
            return redirect("teacher_list")

        teacher = get_object_or_404(CustomUser, id=pending_lesson['teacher_id'], role='teacher')

        if "accept" in request.POST:
            lesson_date = dt.strptime(pending_lesson['date'], "%Y-%m-%d").date()
            lesson_time = dt.strptime(pending_lesson['time'], "%H:%M:%S").time() \
                if ":" in pending_lesson['time'] else dt.strptime(pending_lesson['time'], "%H:%M").time()

            LessonRequest.objects.create(
                student=request.user,
                teacher=teacher,
                date=lesson_date,
                time=lesson_time,
                duration_minutes=pending_lesson['duration_minutes'],
                subject_id=pending_lesson['subject_id'],
                status="pending",
            )
            messages.success(request, "Lesson confirmed and saved successfully!")
            del request.session['pending_lesson']
            return redirect("calendar")

        elif "cancel" in request.POST:
            messages.info(request, "Lesson request was canceled.")
            del request.session['pending_lesson']
            return redirect("book_lesson", teacher_id=teacher.id)

    return redirect("teacher_list")



@login_required
def lesson_calendar_json(request):
    teacher_id = request.GET.get('teacher_id')
    events = []

    if teacher_id:
        teacher_user = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
    else:
        teacher_user = request.user if request.user.role == 'teacher' else None

    if teacher_user:
        lessons = LessonRequest.objects.filter(
            teacher=teacher_user,
            status__in=['pending', 'accepted']
        )
        merged_availabilities = get_merged_availabilities(teacher_user)
    else:  # student view
        lessons = LessonRequest.objects.filter(
            student=request.user,
            status__in=['pending', 'accepted']
        )
        merged_availabilities = {}

    # Dodajemy lekcje (czerwone / blokady)
    for lesson in lessons:
        start_dt = datetime.combine(lesson.date, lesson.time)
        end_dt = start_dt + timedelta(minutes=lesson.duration_minutes)

        if request.user.role == 'student' and lesson.student != request.user:
            events.append({
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'display': 'background',
                'color': 'rgba(255, 204, 204, 0)',
                'type': 'blocked'
            })
        else:
            subject_name = lesson.subject.name if lesson.subject else "Lesson"
            other_person = lesson.teacher if request.user.role == 'student' else lesson.student
            full_name = f"{other_person.first_name} {other_person.last_name}".strip() or "No Name"

            events.append({
                'title': f"{subject_name} with {full_name}",
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'color': '#dc3545',
                'type': 'lesson'
            })

    # Dodajemy dostępności (zielone tylko w wolnych slotach)
    today = datetime.today()
    day_names = ['mon','tue','wed','thu','fri','sat','sun']

    for i in range(0, 366):
        current_day = today + timedelta(days=i)
        dow = current_day.weekday()
        day_name = day_names[dow]

        if day_name in merged_availabilities:
            for start_time, end_time in merged_availabilities[day_name]:
                start_dt = datetime.combine(current_day.date(), start_time)
                end_dt = datetime.combine(current_day.date(), end_time)
                events.append({
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'display': 'background',
                    'color': '#28a745',
                    'type': 'availability'
                })

    return JsonResponse(events, safe=False)



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