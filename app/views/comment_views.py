from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from app.models import Comment, Event


@login_required
def add_comment(request, id):
    """
    Agrega un comentario a un evento.
    Se espera que el formulario de comentario envíe un POST con los campos 'title' y 'text'.
    
    Si el usuario no está autenticado, redirige a la página de inicio de sesión.
    
    Si el comentario se publica correctamente, redirige a la página de detalles del evento.
    
    Si hay un error, muestra un mensaje de error.
    """
    event = get_object_or_404(Event, pk=id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')
        
        if title and text:
            Comment.objects.create(
                user=request.user,
                event=event,
                title=title,
                text=text
            )
            messages.success(request, 'El comentario ha sido publicado correctamente.')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
            
    return redirect('event_detail', id=event.pk)