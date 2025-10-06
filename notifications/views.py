from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.http import require_POST

@login_required
def notifications_json(request):
    notifs = Notification.objects.filter(user=request.user, is_read=False).order_by("-created_at")
    data = [
        {"id": n.id, "message": n.message, "created_at": n.created_at.isoformat()}
        for n in notifs
    ]
    return JsonResponse(data, safe=False)

@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})
