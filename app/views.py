import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Location


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
    return render(request, "app/event_detail.html", {"event": event})


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
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        location_id = request.POST.get("location")
        location = Location.objects.filter(id=location_id).first() if location_id else None


        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user, location)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, location)

        return redirect("events")
    
    
    event = {}
    locations = Location.objects.all()

    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "locations": locations},
    )



@login_required
def list_locations(request):
    locations = Location.objects.all() # Las más nuevas primero
    return render(request, 'locations/list_locations.html', {'locations': locations})

@login_required
def create_location(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        # Validar datos
        errors = Location.validate(name, address, city, int(capacity) if capacity else None, contact)

        if errors:
            # Si hay errores, renderizamos el formulario otra vez, mostrando errores
            return render(request, 'locations/create_location.html', {
                'errors': errors,
                'form_data': request.POST,
            })

        # Si no hay errores, creamos la Location
        Location.new(name, address, city, int(capacity), contact)
        return redirect('locations_list')  # Redirigimos a una lista o donde quieras

    return render(request, 'locations/create_location.html')

def update_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        errors = Location.validate(name, address, city, int(capacity) if capacity else None, contact)

        if errors:
            return render(request, 'locations/update_location.html', {
                'location': location,
                'errors': errors,
                'form_data': request.POST,
            })

        location.update(name=name, address=address, city=city, capacity=int(capacity), contact=contact)
        return redirect('locations_list')

    return render(request, 'locations/update_location.html', {'location': location})

def delete_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    location.delete()
    return redirect('locations_list')
