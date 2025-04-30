import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import CategoryForm

from .models import Category, Event, User


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
    
    categories = Category.objects.filter(is_active=True)
    event_categories = []
    event = {}

    if id is not None:
        event = get_object_or_404(Event, pk=id)
        event_categories = [category.id for category in event.categories.all()]

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        categories = request.POST.getlist("categories")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user, categories)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, categories)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,
            "event_categories": event_categories,
            "user_is_organizer": request.user.is_organizer
        },
    )


def is_organizer(user):
    return user.is_organizer

@login_required
def categories(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'app/categories.html', {'categories': categories})

@login_required
def category_form(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"
        
        success, result = Category.new(name, description, is_active)
        
        if success:
            return redirect('categories')
        
        return render(request, 'app/category_form.html', {
            'errors': result,
            'data': {
                'name': name,
                'description': description,
                'is_active': is_active
            }
        })
        
    return render(request, 'app/category_form.html', {
        'data': {
            'is_active': True  # Por defecto activa
        }
    })

@login_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"
        
        success, errors = category.update(
            name=name,
            description=description,
            is_active=is_active
        )
        
        if success:
            return redirect('categories')
            
        return render(request, 'app/category_form.html', {
            'category': category,
            'errors': errors,
            'data': {
                'name': name,
                'description': description,
                'is_active': is_active
            }
        })
    
    return render(request, 'app/category_form.html', {
        'category': category,
        'data': {
            'name': category.name,
            'description': category.description,
            'is_active': category.is_active
        }
    })

@login_required
def category_delete(request, category_id):
    if request.method == "POST":
        category = get_object_or_404(Category, id=category_id)
        category.delete()
    return redirect('categories')
