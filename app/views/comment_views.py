from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from app.models import Comment, Event


@login_required
def view_comments(request, event_id=None):
    """
    Vista para mostrar los comentarios. Si el usuario es organizador,
    muestra los comentarios de sus eventos en formato tabla. Si no, muestra solo
    los comentarios del evento específico.
    """
    if request.user.is_organizer:
        # Para organizadores, mostrar comentarios de sus eventos
        organizer_events = Event.objects.filter(organizer=request.user)
        comments = Comment.objects.filter(event__in=organizer_events).order_by('-created_at')
        template = 'app/comments/comments_section_organizer.html'
        context = {
            'comments': comments,
            'event': None
        }
    else:
        # Para usuarios normales, mostrar comentarios del evento específico
        if not event_id:
            return redirect('events')
        event = get_object_or_404(Event, pk=event_id)
        comments = Comment.objects.filter(event=event)
        template = 'app/comments/comments_section.html'
        context = {
            'comments': comments,
            'event': event
        }
    
    return render(request, template, context)

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

@login_required
def delete_comment(request, comment_id, event_id=None):
    """
    Elimina un comentario. Solo el organizador o el dueño del comentario pueden eliminarlo.
    """
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # Verificar permisos
    if not (request.user.is_organizer or request.user == comment.user):
        messages.error(request, 'No tienes permiso para eliminar este comentario.')
        if event_id:
            return redirect('event_detail', id=event_id)
        return redirect('view_comments')
        
    comment.delete()
    messages.success(request, 'Comentario eliminado correctamente.')
    
    # Redirigir según el contexto
    if event_id:
        return redirect('event_detail', id=event_id)
    return redirect('view_comments')

@login_required
def edit_comment(request, event_id, comment_id):
    """
    Edita un comentario. Solo el propietario del comentario puede editarlo.
    """
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # Verificar que el usuario sea el propietario del comentario
    if request.user != comment.user:
        messages.error(request, 'No tienes permiso para editar este comentario.')
        return redirect('event_detail', id=event_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')
        
        if title and text:
            comment.title = title
            comment.text = text
            comment.save()
            messages.success(request, 'El comentario ha sido actualizado correctamente.')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
            
    return redirect('event_detail', id=event_id)