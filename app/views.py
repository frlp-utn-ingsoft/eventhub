import datetime

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        selected_categories = request.POST.getlist("categories")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            success, errors = Event.new(title, description, scheduled_at, request.user)
            if success:
                event = Event.objects.get(title=title, organizer=request.user)
                event.categories.set(selected_categories)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)
            event.categories.set(selected_categories)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "categories": categories, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def categories(request):
    categories = Category.objects.all()
    return render(
        request,
        "app/categories.html",
        {
            "categories": categories,
            "user_is_organizer": request.user.is_organizer,
        }
    )


@login_required
def category_form(request, id=None):
    if not request.user.is_organizer:
        return redirect("categories")

    category = get_object_or_404(Category, pk=id) if id else None

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        errors = Category.validate(name)

        if id and Category.objects.filter(name__iexact=name).exclude(pk=id).exists():
            errors["name"] = "Ya existe otra categoría con ese nombre"

        if errors:
            return render(request, "app/category_form.html", {
                "error": list(errors.values())[0],  # Mostrar solo un error
                "category": {
                    "name": name,
                    "description": description,
                    "is_active": is_active,
                },
                "is_edit": category is not None,
            })

        if category:
            category.name = name
            category.description = description
            category.is_active = is_active
            category.save()
        else:
            Category.objects.create(name=name, description=description, is_active=is_active)

        return redirect("categories")

    return render(request, "app/category_form.html", {
        "category": category,
        "is_edit": category is not None,
    })


@login_required
def category_delete(request, id):
    if not request.user.is_organizer:
        return redirect("categories")

    category = get_object_or_404(Category, pk=id)

    if request.method == "POST":
        category.delete()
        return redirect("categories")

    return redirect("categories")

@login_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)
    return render(request, "app/category_detail.html", {"category": category})

