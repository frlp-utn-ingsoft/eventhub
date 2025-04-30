from .models import Notification

def unread_notifications(request):
    """
    Devuelve la cantidad de notificaciones no leídas del usuario autenticado.
    """
    if not request.user.is_authenticated:
        return {"unread_notifications": 0}

    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    return {"unread_notifications": count}
