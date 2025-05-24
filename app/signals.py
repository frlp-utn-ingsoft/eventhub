from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Event

@receiver(pre_save, sender=Event)
def detect_event_update(sender, instance, **kwargs):
    if not instance.pk:
        return  

    try:
        previous = Event.objects.get(pk=instance.pk)
    except Event.DoesNotExist:
        return

    changes = []

    if instance.scheduled_at != previous.scheduled_at:
        changes.append(("scheduled_at", previous.scheduled_at, instance.scheduled_at))

    if instance.venue != previous.venue:
        changes.append(("venue", previous.venue.name if previous.venue else "N/A", instance.venue.name if instance.venue else "N/A"))

    instance._detected_changes = changes if changes else None
