import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count
from .models import Event, User, Category
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import NotificationForm
from .models import Notification
from django.views import generic
from django.urls import reverse_lazy
from django.views import View
from django.http import JsonResponse
from django.template.loader import render_to_string

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

    categories = Category.objects.filter(is_active=True)                        # ADD ----- crud-category

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        category_ids = request.POST.getlist("categories")                       # ADD ----- crud-category

        # Convertir fecha y hora
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")
        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        # Buscar las categorías seleccionadas
        selected_categories = Category.objects.filter(id__in=category_ids)

        if id is None:                                                                                                  # ADD ----- crud-category
            # Crear nuevo evento
            success, errors = Event.new(title, description, scheduled_at, user, selected_categories)

            if not success:
                # Si hay errores, volver al formulario
                return render(
                    request,
                    "app/event_form.html",
                    {
                        "event": {},
                        "categories": categories,
                        "selected_categories": category_ids,
                        "errors": errors,
                        "user_is_organizer": user.is_organizer,
                    },
                )
        else:
            # Editar evento existente
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, user, selected_categories)                   # ADD ----- crud-category

        return redirect("events")

    event = {}
    selected_categories = []
    if id is not None:
        event = get_object_or_404(Event, pk=id)
        selected_categories = event.categories.values_list('id', flat=True)

    return render(                                                                                      # ADD ----- crud-category
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,
            "selected_categories": selected_categories,             
            "user_is_organizer": user.is_organizer,
        },
    )

################### crud-category ###################
@login_required
def categories(request):
    # Contamos los eventos por categoría usando annotate
    categories = Category.objects.annotate(event_count=Count('events')).order_by("name")

    return render(
        request,
        "category/categories.html",
        {
            "categories": categories,  
            "user_is_organizer": request.user.is_organizer,
        },
    )

@login_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)
    return render(
        request,
        "category/category_detail.html",
        {"category": category, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def category_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        category = get_object_or_404(Category, pk=id)
        category.delete()
        return redirect("categories")

    return redirect("categories")

@login_required
def category_form(request, id=None):                    # En la misma def esta el crear y editar.
    user = request.user

    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"

        if id is None:
            # Crear
            Category.objects.create(
                name=name,
                description=description,
                is_active=is_active
            )
        else:
            # Editar
            category = get_object_or_404(Category, pk=id)
            category.name = name
            category.description = description
            category.is_active = is_active
            category.save()

        return redirect("categories")

    category = {}
    if id is not None:
        category = get_object_or_404(Category, pk=id)

    return render(
        request,
        "category/category_form.html",
        {"category": category, "user_is_organizer": request.user.is_organizer},
    )


class OrganizerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_organizer


class NotificationList(LoginRequiredMixin, generic.ListView):
    template_name = "notifications/list.html"
    paginate_by   = 10

    def get_queryset(self):
        return self.request.user.notifications.all()

class NotificationCreate(OrganizerRequiredMixin, generic.CreateView):
    model       = Notification
    form_class  = NotificationForm
    template_name = "notifications/form.html" 
    success_url = reverse_lazy("notifications_list")

class NotificationUpdate(OrganizerRequiredMixin, generic.UpdateView):
    model       = Notification
    form_class  = NotificationForm
    template_name = "notifications/form.html" 
    success_url = reverse_lazy("notifications_list")

class NotificationDelete(OrganizerRequiredMixin, generic.DeleteView):
    model       = Notification
    template_name = "notifications/confirm_delete.html"
    success_url = reverse_lazy("notifications_list")


class NotificationMarkRead(LoginRequiredMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return redirect("notifications_list")
    
class NotificationDropdown(LoginRequiredMixin, View):
    def get(self, request):
        notifs = (request.user.notifications
                    .order_by("-created_at")[:5])
        html = render_to_string(
            "notifications/_dropdown_items.html",
            {"notifs": notifs},
            request=request,
        )
        return JsonResponse({"html": html})