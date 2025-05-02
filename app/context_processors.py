from .models import Notification
from .models import Event  # si hace falta
from django.db.models import Q

def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications": 0}

    user_events = Event.objects.filter(tickets__user=request.user)
    count = Notification.objects.filter(
        is_read=False
    ).filter(
        Q(user=request.user) |
        Q(to_all_event_attendees=True, event__in=user_events)
    ).distinct().count()

    return {"unread_notifications": count}