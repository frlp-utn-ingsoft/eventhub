from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from app.models import Rating
  
@login_required
def create_rating(request, event):
    """
    Esta función maneja la lógica para guardar una calificación
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        stars = request.POST.get('stars')
        comment = request.POST.get('comment')

        # Guardar la nueva calificación en la base de datos
        Rating.objects.create(
            event=event,
            user=request.user,  # Asumimos que el usuario está logueado
            title=title,
            rating=stars,
            text=comment
        )
        return True
    return False

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


@login_required
def eliminar_rating(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)

    # Solo el autor o un organizador puede eliminar
    if request.user == rating.user or request.user.is_organizer:
        rating.delete()

    return redirect(request.META.get('HTTP_REFERER', '/'))
