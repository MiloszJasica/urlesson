from datetime import datetime, timedelta
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from .forms import RecurringAvailabilityForm
from django.utils import timezone
from datetime import timezone as dt_timezone
from .forms import LessonRequestForm, TeacherDayOffForm
from .models import CustomUser, LessonRequest, TeacherAvailabilityPeriod
from accounts.models import Teacher
from .models import (
    TeacherDayOff
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
                        start_dt = datetime.combine(current_date, start_time).replace(tzinfo=dt_timezone.utc)
                        end_dt = datetime.combine(current_date, end_time).replace(tzinfo=dt_timezone.utc)

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
        elif 'delete_recurring' in request.POST:
            recurring_form = RecurringAvailabilityForm(request.POST)
            if recurring_form.is_valid():
                days_of_week = recurring_form.cleaned_data['days_of_week']
                start_time = recurring_form.cleaned_data['start_time']
                end_time = recurring_form.cleaned_data['end_time']
                start_date = recurring_form.cleaned_data['start_date']
                end_date = recurring_form.cleaned_data['end_date']

                current_date = start_date
                deleted_slots = 0

                while current_date <= end_date:
                    weekday_index = str(current_date.weekday())
                    if weekday_index in days_of_week:
                        start_dt = datetime.combine(current_date, start_time).replace(tzinfo=dt_timezone.utc)
                        end_dt = datetime.combine(current_date, end_time).replace(tzinfo=dt_timezone.utc)

                        slots = TeacherAvailabilityPeriod.objects.filter(
                            teacher=request.user,
                            start_datetime__lt=end_dt,
                            end_datetime__gt=start_dt
                        )

                        for slot in slots:
                            if slot.start_datetime >= start_dt and slot.end_datetime <= end_dt:
                                slot.delete()
                                deleted_slots += 1
                                continue

                            if slot.start_datetime < start_dt and slot.end_datetime > end_dt:
                                TeacherAvailabilityPeriod.objects.create(
                                    teacher=request.user,
                                    start_datetime=slot.start_datetime,
                                    end_datetime=start_dt
                                )
                                TeacherAvailabilityPeriod.objects.create(
                                    teacher=request.user,
                                    start_datetime=end_dt,
                                    end_datetime=slot.end_datetime
                                )
                                slot.delete()
                                deleted_slots += 1
                                continue

                            if slot.start_datetime < end_dt <= slot.end_datetime:
                                slot.start_datetime = end_dt
                                slot.save()
                                deleted_slots += 1
                                continue

                            if slot.start_datetime <= start_dt < slot.end_datetime:
                                slot.end_datetime = start_dt
                                slot.save()
                                deleted_slots += 1
                                continue

                    current_date += timedelta(days=1)

                if deleted_slots > 0:
                    messages.success(request, f"Deleted or adjusted {deleted_slots} availability slot(s).")
                else:
                    messages.info(request, "No availability found to delete.")
            else:
                messages.error(request, "Form is invalid. Please check your input.")

            return redirect('teacher_availability')


    teacher = request.user
    periods = TeacherAvailabilityPeriod.objects.filter(teacher=teacher)
    days_off = TeacherDayOff.objects.filter(teacher=teacher).order_by("date")

    lessons = LessonRequest.objects.filter(
        teacher=teacher,
        status__in=['pending', 'accepted']
    ).select_related("student", "subject").order_by("date", "time")

    return render(request, 'calendar.html', {
        'day_off_form': day_off_form,
        'availability_periods': periods,
        'days_off': days_off,
        'recurring_form': recurring_form,
        'teacher': teacher,
        'lessons': lessons,
    })


@login_required
def teacher_availability_json(request):
    teacher_id = request.GET.get("teacher_id") or request.user.id
    teacher = get_object_or_404(CustomUser, id=teacher_id, role="teacher")

    events = []

    periods = TeacherAvailabilityPeriod.objects.filter(teacher=teacher)
    for p in periods:
        events.append({
            "id": f"avail-{p.id}",
            "start": p.start_datetime.isoformat(),
            "end": p.end_datetime.isoformat(),
            "color": "#28a745",
            "display": "background",
            "type": "availability"
        })

    lessons = LessonRequest.objects.filter(
        teacher=teacher,
        status__in=['pending', 'accepted']
    ).select_related("student", "subject")

    for lesson in lessons:
        start_dt = timezone.make_aware(datetime.combine(lesson.date, lesson.time), dt_timezone.utc)
        end_dt = start_dt + timedelta(minutes=lesson.duration_minutes)

        color_map = {
            "pending": "#dc3545",   # red
            "accepted": "#28a745",  # green
            "rejected": "#6c757d"   # grey
        }

        events.append({
            "id": f"lesson-{lesson.id}",
            "title": f"{lesson.subject.name if lesson.subject else 'Lesson'} with {lesson.student.get_full_name()}",
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "color": color_map.get(lesson.status, "#007bff"),
            "type": "lesson",
            "status": lesson.status
        })


    return JsonResponse(events, safe=False)


@csrf_exempt
def add_availability(request):
    if request.method == "POST":
        data = json.loads(request.body)
        start_str = data.get("start")
        end_str = data.get("end")
        teacher_id = data.get("teacher_id")

        start = parse_datetime(start_str)
        end = parse_datetime(end_str)

        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone=timezone.utc)
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone=timezone.utc)

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

@login_required
def delete_availability(request):
    if request.method == "POST":
        data = json.loads(request.body)
        availability_id = data.get("id")

        # jeśli id ma formę "avail-123", wyciągnij numer
        if isinstance(availability_id, str) and availability_id.startswith("avail-"):
            availability_id = int(availability_id.replace("avail-", ""))

        TeacherAvailabilityPeriod.objects.filter(id=availability_id, teacher=request.user).delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

# ---------------------------
# Lesson Booking
# ---------------------------

def is_slot_available_utc(teacher, lesson_start, lesson_end):
    periods = TeacherAvailabilityPeriod.objects.filter(teacher=teacher)

    for period in periods:
        if lesson_start >= period.start_datetime and lesson_end <= period.end_datetime:
            conflicting_lessons = LessonRequest.objects.filter(
                teacher=teacher,
                status__in=['pending', 'accepted']
            )
            for lesson in conflicting_lessons:
                existing_start = datetime.combine(lesson.date, lesson.time, tzinfo=dt_timezone.utc)
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
                lesson_date = datetime.strptime(request.POST.get('selected_date'), "%Y-%m-%d").date()
                lesson_time = datetime.strptime(request.POST.get('selected_time'), "%H:%M").time()
                lesson_start = datetime.combine(lesson_date, lesson_time, tzinfo=dt_timezone.utc)
                lesson_end = lesson_start + timedelta(minutes=lesson.duration_minutes)
            except (TypeError, ValueError):
                form.add_error(None, "Invalid date or time format.")
                return render(request, 'book_lesson.html', {'form': form, 'teacher': teacher, 'subject_list': subject_list})

            lesson.subject_id = request.POST.get("subject")

            if not is_slot_available_utc(teacher, lesson_start, lesson_end):
                messages.error(request, "Selected time is unavailable. Please choose a green time slot.")
                return render(request, 'book_lesson.html', {'form': form, 'teacher': teacher, 'subject_list': subject_list})

            lesson.date = lesson_date
            lesson.time = lesson_time
            lesson.status = "pending"
            lesson.save()
            messages.success(request, "Lesson successfully booked!")
            return redirect('student_calendar')
    else:
        form = LessonRequestForm(teacher=teacher)

    return render(request, 'book_lesson.html', {
        'form': form,
        'teacher': teacher,
        'subject_list': subject_list,
        'price_individual': getattr(teacher.teacher_profile, 'price_per_minute_individual', 0),
    })

@login_required
@csrf_exempt
def update_lesson_status(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lesson_id = data.get("id")
        action = data.get("action")

        lesson = get_object_or_404(LessonRequest, id=lesson_id, teacher=request.user)

        if lesson.status == "pending":
            if action == "accept":
                lesson.status = "accepted"
                lesson.save()
                messages.success(request, "Lesson accepted.")
                return JsonResponse({"success": True, "status": "accepted"})

            elif action == "reject":
                lesson.status = "rejected"
                messages.success(request, "Lesson rejected.")
                lesson.save()
                return JsonResponse({"success": True, "status": "rejected"})

            # elif action == "reschedule":
            #     new_start = parse_datetime(data.get("new_start"))
            #     new_end = parse_datetime(data.get("new_end"))

            #     if new_start and new_end:
            #         lesson.date = new_start.date()
            #         lesson.time = new_start.time()
            #         lesson.status = "pending"
            #         lesson.save()
            #         return JsonResponse({"success": True, "status": "pending"})

            #     return JsonResponse({"success": False, "error": "Invalid datetime"}, status=400)

            return JsonResponse({"success": False, "error": "Invalid action"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

@login_required
@csrf_exempt
def update_lesson_status_student(request):
    if request.method == "POST":
        data = json.loads(request.body)
        lesson_id = data.get("id")
        action = data.get("action")

        lesson = get_object_or_404(LessonRequest, id=lesson_id, student=request.user)

        if lesson.status == "pending" and action == "cancel":
            messages.success(request, "Lesson successfully canceled.")
            lesson.status = "canceled"
            lesson.save()

            return JsonResponse({"success": True, "status": "canceled"})

        return JsonResponse({"success": False, "error": "Invalid action or status"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

# ---------------------------
# Student Calendar
# ---------------------------

@login_required
def student_calendar_view(request):
    lessons = LessonRequest.objects.filter(
        student=request.user,
        status__in=['pending', 'accepted']
    ).select_related("teacher", "subject")

    return render(request, "student_calendar.html", {
        "lessons": lessons,
        "student": request.user,
    })


@login_required
def student_calendar_json(request):
    lessons = LessonRequest.objects.filter(
        student=request.user,
        status__in=['pending', 'accepted']
    ).select_related("teacher", "subject")

    events = []
    color_map = {
            "pending": "#007bff",   # blue
            "accepted": "#28a745",  # green
            "rejected": "#6c757d",   # grey
            "canceled": "#6c757d"   # grey
        }
        
    for lesson in lessons:
        start_dt = timezone.make_aware(datetime.combine(lesson.date, lesson.time), dt_timezone.utc)
        end_dt = start_dt + timedelta(minutes=lesson.duration_minutes)
        events.append({
            "id": f"lesson-{lesson.id}",
            "title": f"{lesson.subject.name if lesson.subject else 'Lesson'} with {lesson.teacher.get_full_name()}",
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "color": color_map.get(lesson.status, "#007bff"),
            "type": "lesson",
            "status": lesson.status,
        })

    return JsonResponse(events, safe=False)


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
            lesson_start = datetime.combine(lesson.date, lesson.time, tzinfo=dt_timezone.utc)
            lesson_end = lesson_start + timedelta(minutes=lesson.duration_minutes)

            new_free_slots = []
            for slot_start, slot_end in free_slots:
                if slot_start.tzinfo is None:
                    slot_start = slot_start.replace(tzinfo=dt_timezone.utc)
                if slot_end.tzinfo is None:
                    slot_end = slot_end.replace(tzinfo=dt_timezone.utc)

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

        for slot_start, slot_end in free_slots:
            events.append({
                'start': slot_start.isoformat(),
                'end': slot_end.isoformat(),
                'display': 'background',
                'color': '#28a745',
                'type': 'availability'
            })

    for lesson in lessons.filter(student=request.user):
        start_dt = datetime.combine(lesson.date, lesson.time, tzinfo=dt_timezone.utc)
        end_dt = start_dt + timedelta(minutes=lesson.duration_minutes)
        subject_name = lesson.subject.name if lesson.subject else "Lesson"
        events.append({
            'title': subject_name,
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
            'color': '#dc3545',
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