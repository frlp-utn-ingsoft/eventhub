from .models import Notification

#para que el template base pueda fijarse si el usuario tiene notificaciones sin leer y le cambie el color a la campana

def notification_icon(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(addressee=request.user, is_read=False).count()
        icon = f'<i class="bi bi-bell{"-fill text-danger" if unread_count > 0 else ""}"></i>'
        return {'icon': icon}
    return {'icon': '<i class="bi bi-bell"></i>'}
