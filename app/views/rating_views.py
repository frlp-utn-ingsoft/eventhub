from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from ..models import Rating, Ticket


@login_required
def create_rating(request, event):
    """
    Esta función maneja la lógica para guardar una calificación.
    Solo permite calificar si el usuario tiene un ticket para el evento.
    """
    # Verificar si el usuario tiene un ticket para este evento
    # guardamos el booleano en una variable
    has_ticket = Ticket.objects.filter(event=event, user=request.user).exists()
    
    if not has_ticket:
        messages.error(request, 'Solo los usuarios con entrada pueden calificar el evento.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if request.method == 'POST':
        title = request.POST.get('title')
        stars = request.POST.get('stars')
        comment = request.POST.get('comment')

        # Guardar la nueva calificación en la base de datos
        Rating.objects.create(
            event=event,
            user=request.user,
            title=title,
            rating=stars,
            text=comment
        )
        messages.success(request, 'Tu calificación ha sido guardada correctamente.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def editar_rating(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)


    if request.method == 'POST':
        if (request.user == rating.user or not request.user.is_organizer):
            rating.title = request.POST.get('title')
            rating.rating = int(request.POST.get('stars'))
            rating.text = request.POST.get('comment')
            rating.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def eliminar_rating(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)

    # Solo el autor, o un organizador puede eliminar
    if (request.user == rating.user) or request.user.is_organizer:
        rating.delete()
        messages.success(request, 'La calificación ha sido eliminada correctamente.')

    return redirect(request.META.get('HTTP_REFERER', '/'))
