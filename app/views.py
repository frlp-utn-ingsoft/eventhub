import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Event, User, Rating, Category
from .forms import RatingForm, CategoryForm
from django.db.models import Count
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

    fecha = request.GET.get("fecha")
    categoria_id = request.GET.get("categoria")

    if fecha:
        events = events.filter(scheduled_at__date=fecha)
    if categoria_id:
        events = events.filter(categories__id=categoria_id)

    events = events.distinct()

    categorias = Category.objects.all()
    return render(
        request,
        "app/events.html",
        {"events": events,
         "user_is_organizer": request.user.is_organizer, 
         "categorias": categorias,
        },
    )

@login_required
def rating_create(request, id):
    if request.user.is_organizer:
        messages.error(request, "Los organizadores no pueden dejar calificaciones.")
        return redirect("event_detail", id=id)

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        title = request.POST.get("title", "").strip()
        score = request.POST.get("score")
        comment = request.POST.get("comment", "").strip()

        Rating.objects.create(
            event=event, user=request.user, title=title, score=score, comment=comment
        )

    return redirect("event_detail", id=id)

@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    ratings = Rating.objects.filter(event=event)
    user_is_organizer = event.organizer == request.user

    rating_to_edit = None
    rating_id = request.GET.get('rating_id') or request.POST.get('rating_id')

    if rating_id:
        rating_to_edit = get_object_or_404(Rating, pk=rating_id, event=event)
        if user_is_organizer or rating_to_edit.user != request.user:
            return redirect('event_detail', id=id)

    if request.method == 'POST':
        if rating_to_edit:
            form = RatingForm(request.POST, instance=rating_to_edit)
        else:
            if user_is_organizer:
                return redirect('event_detail', id=id)
            form = RatingForm(request.POST)

        if form.is_valid():
            new_rating = form.save(commit=False)
            new_rating.event = event
            new_rating.user = request.user
            new_rating.save()
            return redirect('event_detail', id=id)
    else:
        form = RatingForm(instance=rating_to_edit)

    context = {
        'event': event,
        'ratings': ratings,
        'form': form,
        'rating_to_edit': rating_to_edit,
        'user_is_organizer': user_is_organizer,
        'show_rating_form': not user_is_organizer
    }
    return render(request, 'app/event_detail.html', context)


@login_required
def rating_delete(request, id, rating_id):
    event = get_object_or_404(Event, pk=id)
    rating = get_object_or_404(Rating, pk=rating_id, event=event)
    if request.user == rating.user or request.user.is_organizer:
        if request.method == "POST":
            rating.delete()
            return redirect("event_detail", id=id)
    return redirect("event_detail", id=id)

@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    event = get_object_or_404(Event, pk=id)

    if request.method == "POST":
        event.delete()
        return redirect("events")

    return redirect("event_detail", id=id)

@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    categories = Category.objects.all()
    selected_categories = []

    event = None

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        selected_categories = [
            int(cat_id) for cat_id in request.POST.getlist("categories") if cat_id.isdigit()
        ]

        [year, month, day] = map(int, date.split("-"))
        [hour, minutes] = map(int, time.split(":"))

        scheduled_at = timezone.make_aware(
            datetime.datetime(year, month, day, hour, minutes)
        )

        today = timezone.localtime().date()
        if scheduled_at.date() <= today:
            return render(
                request,
                "app/event_form.html",
                {
                    "event": event,
                    "categories": categories,
                    "user_is_organizer": request.user.is_organizer,
                    "error": "La fecha debe ser a partir de mañana.",
                    "min_date": (today + datetime.timedelta(days=1)),
                },
            )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    if id is not None:
        event = get_object_or_404(Event, pk=id)

    today = timezone.localtime().date()
    min_date = today + datetime.timedelta(days=1)

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,  
            "selected_categories": selected_categories,  
            "user_is_organizer": request.user.is_organizer,
            "min_date": min_date
        },
    )

@login_required
def category_list(request):
    if request.user.is_organizer:
        categories = Category.objects.all().annotate(event_count=Count('events'))
    else:
        categories = Category.objects.filter(is_active=True).annotate(event_count=Count('events'))

    return render(
        request,
        'app/category_list.html',
        {'categories': categories, 'user_is_organizer': request.user.is_organizer}
    )

@login_required
def category_form(request, id=None):
    if not request.user.is_organizer:
        return redirect('category_list') 

    if id:
        category = get_object_or_404(Category, pk=id)
    else:
        category = None

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            if id:
                messages.success(request, 'La categoría fue actualizada con éxito')
            else:
                messages.success(request, 'La categoría fue creada con éxito')
            return redirect('category_list') 
    else:
        form = CategoryForm(instance=category)

    return render(request, 'app/category_form.html', {'form': form})

@login_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)
    return render(request, 'app/category_detail.html', {
        'category': category,
        'user_is_organizer': request.user.is_organizer
    })

@login_required
def category_delete(request, id):
    if not request.user.is_organizer:
        return redirect('category_list')  

    category = get_object_or_404(Category, pk=id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'La categoría fue eliminada con éxito')
        return redirect('category_list')  
    return redirect('category_list')
