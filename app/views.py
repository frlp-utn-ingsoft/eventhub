import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count
from django.http import HttpResponseForbidden
from .models import Event, User, Category, Comment, Venue
from django.contrib import messages


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    todos_los_comentarios = Comment.objects.filter(event=event).order_by('-created_at')

    return render(request, "app/event_detail.html", {"event": event, "todos_los_comentarios": todos_los_comentarios,})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        id = request.POST.get("id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        category_id = request.POST.get("category")
        venue_id = request.POST.get("venue")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        category = get_object_or_404(Category, pk=category_id)
        venue = get_object_or_404(Venue, pk=venue_id)

        if id is None:
            success, errors = Event.new(title, description, scheduled_at, request.user, category, venue)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, category, venue)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.filter(is_active=True)
    venues = Venue.objects.all()

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categories": categories, "venues": venues},
    )


def categorias(request):
    category_list = Category.objects.annotate(num_events=Count('events'))

    return render(request, "app/categories.html",
                    {"categorys": category_list, "user_is_organizer": request.user.is_organizer})

def category_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        category = Category.objects.create(name=name, description=description)

        return redirect('categorias')

    return render(request, 'app/category_form.html')

def edit_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name and description:
            category.name = name
            category.description = description
            category.save()
            return redirect('categorias')
        else:
            return render(request, 'app/category_edit.html', {
                'category': category,
                'error': 'Todos los campos son obligatorios.'
            })

    return render(request, 'app/category_edit.html', {'category': category})

def category_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("categorias")

    if request.method == "POST":
        category = get_object_or_404(Category, pk=id)
        category.delete()
        return redirect("categorias")

    return redirect("categorias")



def crear_comentario(request, event_id):
    evento = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        text = request.POST.get('text', '').strip()
        comentario_id = request.POST.get('comentario_id')  # nuevo

        errors = Comment.validate(title, text)

        if errors:
            return render(request, "app/event_detail.html", {
                "event": evento,
                "errors": errors,
                "title": title,
                "text": text,
            })

        if comentario_id:
            # Si hay comentario_id, es edición
            comentario = get_object_or_404(Comment, id=comentario_id)
            if request.user != comentario.user:
                return HttpResponseForbidden("No podés editar este comentario")

            comentario.update(title, text)
            messages.success(request, "Comentario editado exitosamente")
        else:
            # Si no hay comentario_id, se crea uno nuevo
            Comment.objects.create(
                title=title,
                text=text,
                user=request.user,
                event=evento
            )
            messages.success(request, "Comentario creado exitosamente")

        return redirect('event_detail', id=event_id)

    return redirect('event_detail', id=event_id)



def delete_comment(request, event_id, pk):
    comment = get_object_or_404(Comment, pk=pk, event_id=event_id)

    # Verificación de permisos
    if request.user == comment.user or request.user == comment.event.organizer:
        comment.delete()
        messages.success(request, "Comentario eliminado correctamente")
    else:
        messages.error(request, "No tienes permiso para esta acción")

    return redirect('event_detail', id=event_id)

#------------------VENUES-----------------
#listar venues
@login_required
def venue_list(request):
    if not request.user.is_organizer:
        return redirect('events')

    venues = Venue.objects.all()
    return render(request, 'app/venue_list.html', {'venues': venues, "user_is_organizer": request.user.is_organizer})

#crear venues
def venue_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        capacity = request.POST.get('capacity', '').strip()
        contact = request.POST.get('contact', '').strip()

        errors = []

        # Validaciones
        if not name:
            errors.append('El nombre es obligatorio.')
        if not address:
            errors.append('La dirección es obligatoria.')
        if not city:
            errors.append('La ciudad es obligatoria.')
        if not capacity:
            errors.append('La capacidad es obligatoria.')
        else:
            try:
                capacity = int(capacity)
                if capacity <= 0:
                    errors.append('La capacidad debe ser un número positivo.')
            except ValueError:
                errors.append('La capacidad debe ser un número.')

        if not contact:
            errors.append('El contacto es obligatorio.')

        if errors:
            return render(request, 'app/venue_form.html', {
                'errors': errors,
                'venue': {
                    'name': name,
                    'address': address,
                    'city': city,
                    'capacity': capacity,
                    'contact': contact,
                }
            })

        Venue.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact
        )
        return redirect('venue_list')

    return render(request, 'app/venue_form.html')


# Editar locación existente
def venue_edit(request, pk):
    venue = get_object_or_404(Venue, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        capacity = request.POST.get('capacity', '').strip()
        contact = request.POST.get('contact', '').strip()

        errors = []

        # Validaciones
        if not name:
            errors.append('El nombre es obligatorio.')
        if not address:
            errors.append('La dirección es obligatoria.')
        if not city:
            errors.append('La ciudad es obligatoria.')
        if not capacity:
            errors.append('La capacidad es obligatoria.')
        else:
            try:
                capacity = int(capacity)
                if capacity <= 0:
                    errors.append('La capacidad debe ser un número positivo.')
            except ValueError:
                errors.append('La capacidad debe ser un número.')

        if not contact:
            errors.append('El contacto es obligatorio.')

        if errors:
            return render(request, 'app/venue_form.html', {
                'errors': errors,
                'venue': {
                    'name': name,
                    'address': address,
                    'city': city,
                    'capacity': capacity,
                    'contact': contact,
                }
            })

        venue.name = name
        venue.address = address
        venue.city = city
        venue.capacity = capacity
        venue.contact = contact
        venue.save()

        return redirect('venue_list')

    return render(request, 'app/venue_form.html', {'venue': venue})

#borrar venues
def venue_delete(request, pk):
    venue = get_object_or_404(Venue, pk=pk)

    if request.method == 'POST':
        venue.delete()
        return redirect('venue_list')

    return render(request, 'app/venue_confirm_delete.html', {'venue': venue})