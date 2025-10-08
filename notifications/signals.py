from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonRequest, Notification

@receiver(post_save, sender=LessonRequest)
def lesson_request_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.teacher,
            message=f"New lesson number {instance.id} has been reserved by {instance.student}."
        )
    else:
        if instance.status == "rejected":
            Notification.objects.create(
                user=instance.student,
                message=f"Your lesson number {instance.id} with {instance.teacher} has been rejected."
            )
        elif instance.status == "accepted":
            Notification.objects.create(
                user=instance.student,
                message=f"Your lesson number {instance.id} with {instance.teacher} has been confirmed."
            )
        elif instance.status == "canceled":
            Notification.objects.create(
                user=instance.teacher,
                message=f"The lesson number {instance.id} with {instance.student} has been canceled."
            )