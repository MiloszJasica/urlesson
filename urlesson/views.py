from datetime import datetime, timedelta
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from .forms import RecurringAvailabilityForm
from django.utils.timezone import localtime

from .forms import LessonRequestForm, TeacherDayOffForm
from .models import (
    CustomUser,
    LessonRequest,
    Teacher,
    TeacherDayOff,
    TeacherAvailabilityPeriod
)

# ---------------------------
# Home & Teacher List
# ---------------------------

def home(request):
    return render(request, 'home.html')

def teacher_list_view(request):
    users = CustomUser.objects.filter(role='teacher').select_related('teacher_profile')
    if request.user.is_authenticated:
        users = users.exclude(id=request.user.id)
    return render(request, 'teacher_list.html', {'object_list': users})


# ---------------------------
# Teacher Availability Views
# ---------------------------

@login_required
def teacher_availability_view(request):
    recurring_form = RecurringAvailabilityForm()
    day_off_form = TeacherDayOffForm()
    
    if request.method == 'POST':
        if 'add_day_off' in request.POST:
            day_off_form = TeacherDayOffForm(request.POST)
            if day_off_form.is_valid():
                day_off = day_off_form.save(commit=False)
                day_off.teacher = request.user
                day_off.save()
                messages.success(request, "Day off added successfully.")
                return redirect('teacher_availability')
        
        elif 'add_recurring' in request.POST:
            recurring_form = RecurringAvailabilityForm(request.POST)
            if recurring_form.is_valid():
                days_of_week = recurring_form.cleaned_data['days_of_week']  # np. ['0','2']
                start_time = recurring_form.cleaned_data['start_time']
                end_time = recurring_form.cleaned_data['end_time']
                start_date = recurring_form.cleaned_data['start_date']
                end_date = recurring_form.cleaned_data['end_date']

                current_date = start_date
                merged_slots = 0

                while current_date <= end_date:
                    weekday_index = str(current_date.weekday())
                    if weekday_index in days_of_week:
                        start_dt = timezone.make_aware(datetime.combine(current_date, start_time), timezone.get_current_timezone())
                        end_dt = timezone.make_aware(datetime.combine(current_date, end_time), timezone.get_current_timezone())

                        overlapping = TeacherAvailabilityPeriod.objects.filter(
                            teacher=request.user,
                            start_datetime__lt=end_dt,
                            end_datetime__gt=start_dt
                        )

                        if overlapping.exists():
                            min_start = min([start_dt] + [o.start_datetime for o in overlapping])
                            max_end = max([end_dt] + [o.end_datetime for o in overlapping])
                            overlapping.delete()
                            TeacherAvailabilityPeriod.objects.create(
                                teacher=request.user,
                                start_datetime=min_start,
                                end_datetime=max_end
                            )
                            merged_slots += 1
                        else:
                            TeacherAvailabilityPeriod.objects.create(
                                teacher=request.user,
                                start_datetime=start_dt,
                                end_datetime=end_dt
                            )

                    current_date += timedelta(days=1)

                if merged_slots > 0:
                    messages.success(request, f"{merged_slots} slot(s) were merged with existing availability.")
                else:
                    messages.success(request, "Recurring availability added successfully.")

                return redirect('teacher_availability')
            else:
                messages.error(request, "Form is invalid. Please check the input.")

    teacher = request.user
    periods = TeacherAvailabilityPeriod.objects.filter(teacher=teacher)
    days_off = TeacherDayOff.objects.filter(teacher=teacher).order_by("date")

    return render(request, 'calendar.html', {
        'day_off_form': day_off_form,
        'availability_periods': periods,
        'days_off': days_off,
        'recurring_form': recurring_form,
        'teacher': teacher,
    })


@login_required
def teacher_availability_json(request):
    teacher_id = request.GET.get("teacher_id") or request.user.id
    periods = TeacherAvailabilityPeriod.objects.filter(teacher_id=teacher_id)
    events = []

    for p in periods:
        events.append({
            "id": p.id,
            "start": p.start_datetime.isoformat(),
            "end": p.end_datetime.isoformat(),
            "color": "#28a745",
            "display": "background",
            "type": "availability"
        })

    return JsonResponse(events, safe=False)

@csrf_exempt
def add_availability(request):
    if request.method == "POST":
        data = json.loads(request.body)
        start = parse_datetime(data.get("start"))
        end = parse_datetime(data.get("end"))
        teacher_id = data.get("teacher_id")

        overlapping = TeacherAvailabilityPeriod.objects.filter(
            teacher_id=teacher_id,
            start_datetime__lt=end,
            end_datetime__gt=start
        )

        if overlapping.exists():
            min_start = min([start] + [o.start_datetime for o in overlapping])
            max_end = max([end] + [o.end_datetime for o in overlapping])
            overlapping.delete()
            TeacherAvailabilityPeriod.objects.create(
                teacher_id=teacher_id,
                start_datetime=min_start,
                end_datetime=max_end
            )
        else:
            TeacherAvailabilityPeriod.objects.create(
                teacher_id=teacher_id,
                start_datetime=start,
                end_datetime=end
            )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)

@csrf_exempt
@login_required
def delete_availability(request):
    if request.method == "POST":
        data = json.loads(request.body)
        availability_id = data.get("id")
        TeacherAvailabilityPeriod.objects.filter(id=availability_id, teacher=request.user).delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

# ---------------------------
# Lesson Booking
# ---------------------------

def is_slot_available(teacher, date, time, duration_minutes):
    lesson_start = timezone.make_aware(datetime.combine(date, time))
    lesson_end = lesson_start + timedelta(minutes=duration_minutes)

    periods = TeacherAvailabilityPeriod.objects.filter(teacher=teacher)

    for period in periods:
        if lesson_start >= period.start_datetime and lesson_end <= period.end_datetime:
            conflicting_lessons = LessonRequest.objects.filter(
                teacher=teacher,
                date=date,
                status__in=['pending', 'accepted']
            )
            for lesson in conflicting_lessons:
                existing_start = timezone.make_aware(datetime.combine(lesson.date, lesson.time))
                existing_end = existing_start + timedelta(minutes=lesson.duration_minutes)
                if lesson_start < existing_end and lesson_end > existing_start:
                    return False
            return True
    return False


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
                lesson.date = datetime.strptime(request.POST.get('selected_date'), "%Y-%m-%d").date()
                lesson.time = datetime.strptime(request.POST.get('selected_time'), "%H:%M").time()
            except (TypeError, ValueError):
                form.add_error(None, "Invalid date or time format.")
                return render(request, 'book_lesson.html', {'form': form, 'teacher': teacher, 'subject_list': subject_list})

            lesson.subject_id = request.POST.get("subject")

            if not is_slot_available(teacher, lesson.date, lesson.time, lesson.duration_minutes):
                messages.error(request, "Selected time is unavailable. Please choose a green time slot.")
                return render(request, 'book_lesson.html', {'form': form, 'teacher': teacher, 'subject_list': subject_list})

            lesson.status = "pending"
            lesson.save()
            messages.success(request, "Lesson successfully booked!")
            return redirect('calendar')
    else:
        form = LessonRequestForm(teacher=teacher)

    return render(request, 'book_lesson.html', {
        'form': form,
        'teacher': teacher,
        'subject_list': subject_list,
        'price_individual': getattr(teacher.teacher_profile, 'price_per_minute_individual', 0),
    })


# ---------------------------
# Lesson Calendar
# ---------------------------

@login_required
def lesson_calendar_json(request):
    teacher_id = request.GET.get('teacher_id')
    events = []

    teacher_user = get_object_or_404(CustomUser, id=teacher_id, role='teacher') if teacher_id else None
    if not teacher_user:
        return JsonResponse(events, safe=False)

    lessons = LessonRequest.objects.filter(teacher=teacher_user, status__in=['pending', 'accepted'])

    periods = TeacherAvailabilityPeriod.objects.filter(teacher=teacher_user)

    for period in periods:
        free_slots = [(period.start_datetime, period.end_datetime)]

        for lesson in lessons:
            lesson_start = timezone.make_aware(datetime.combine(lesson.date, lesson.time))
            lesson_end = lesson_start + timedelta(minutes=lesson.duration_minutes)

            new_free_slots = []
            for slot_start, slot_end in free_slots:
                if timezone.is_naive(slot_start):
                    slot_start = timezone.make_aware(slot_start)
                if timezone.is_naive(slot_end):
                    slot_end = timezone.make_aware(slot_end)

                if lesson_end <= slot_start or lesson_start >= slot_end:
                    new_free_slots.append((slot_start, slot_end))
                    continue
                if lesson_start <= slot_start < lesson_end < slot_end:
                    new_free_slots.append((lesson_end, slot_end))
                    continue
                if slot_start < lesson_start < lesson_end < slot_end:
                    new_free_slots.append((slot_start, lesson_start))
                    new_free_slots.append((lesson_end, slot_end))
                    continue
                if lesson_start <= slot_start and lesson_end >= slot_end:
                    continue
                if slot_start < lesson_start < slot_end <= lesson_end:
                    new_free_slots.append((slot_start, lesson_start))
                    continue

            free_slots = new_free_slots


        # Dodajemy zielone sloty
        for slot_start, slot_end in free_slots:
            events.append({
                'start': slot_start.isoformat(),
                'end': slot_end.isoformat(),
                'display': 'background',
                'color': '#28a745',  # zielone
                'type': 'availability'
            })

    # Dodajemy lekcje samego użytkownika (czerwone)
    for lesson in lessons.filter(student=request.user):
        start_dt = datetime.combine(lesson.date, lesson.time)
        end_dt = start_dt + timedelta(minutes=lesson.duration_minutes)
        subject_name = lesson.subject.name if lesson.subject else "Lesson"
        events.append({
            'title': subject_name,
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'color': '#dc3545',  # czerwone
            'type': 'lesson'
        })

    return JsonResponse(events, safe=False)




# ---------------------------
# Misc
# ---------------------------

def lesson_success(request):
    return render(request, 'lesson_success.html')

def confirm_lessons_view(request, teacher_id):
    teacher = get_object_or_404(CustomUser, id=teacher_id, role='teacher')
    if request.user != teacher:
        messages.error(request, "You are not authorized to confirm lessons for this teacher.")
        return redirect('home')

    if request.method == 'POST':
        lesson_ids = request.POST.getlist('lesson_ids')
        action = request.POST.get('action')
        lessons = LessonRequest.objects.filter(id__in=lesson_ids, teacher=teacher, status='pending')

        if action == 'accept':
            lessons.update(status='accepted')
            messages.success(request, f"{lessons.count()} lessons accepted.")
        elif action == 'reject':
            lessons.update(status='rejected')
            messages.success(request, f"{lessons.count()} lessons rejected.")
        else:
            messages.error(request, "Invalid action.")

        return redirect('confirm_lessons', teacher_id=teacher.id)

    pending_lessons = LessonRequest.objects.filter(teacher=teacher, status='pending').order_by('date', 'time')
    return render(request, 'confirm_lessons.html', {'pending_lessons': pending_lessons, 'teacher': teacher})