import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count
from django.views import generic, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.template.loader import render_to_string

from .models import Event, User, Ticket, Category, Notification, RefundRequest
from .forms import TicketForm, CategoryForm, NotificationForm, RefundRequestForm

# ------------------- Registro y login -------------------
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


# ------------------- Eventos -------------------
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
        category_ids = request.POST.getlist("categories")

        # Convertir fecha y hora
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")
        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        selected_categories = Category.objects.filter(id__in=category_ids)

        if id is None:
            success, errors = Event.new(title, description, scheduled_at, user, selected_categories)

            if not success:
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
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, user, selected_categories)

        return redirect("events")

    event = {}
    selected_categories = []
    if id is not None:
        event = get_object_or_404(Event, pk=id)
        selected_categories = event.categories.values_list('id', flat=True)

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,
            "selected_categories": selected_categories,
            "user_is_organizer": user.is_organizer,
        },
    )

# ------------------- Refund -------------------
@login_required
def my_refund_requests(request):
    refunds = RefundRequest.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "app/refund/my_refund_requests.html", {"refunds": refunds})


@login_required
def refund_request_form(request, id=None):
    if id:
        refund = get_object_or_404(RefundRequest, pk=id, user=request.user)
    else:
        refund = None

    if request.method == "POST":
        form = RefundRequestForm(request.POST, instance=refund)
        if form.is_valid():
            refund_request = form.save(commit=False)
            refund_request.user = request.user
            refund_request.save()
            return redirect("my_refund_requests")
    else:
        form = RefundRequestForm(instance=refund)

    return render(request, "app/refund/my_refund_requests.html", {"form": form, "refund": refund})


@login_required
def refund_request_delete(request, id):
    refund = get_object_or_404(RefundRequest, pk=id, user=request.user)
    if request.method == "POST":
        refund.delete()
    return redirect("my_refund_requests")


@login_required
def manage_refund_requests(request):
    if not request.user.is_organizer:
        return redirect("events")

    refunds = RefundRequest.objects.all().order_by("-created_at")
    return render(request, "app/refund/manage_refund_requests.html", {"refunds": refunds})


@login_required
def approve_refund_request(request, id):
    if not request.user.is_organizer:
        return redirect("events")

    refund = get_object_or_404(RefundRequest, pk=id)
    refund.approve()
    return redirect("manage_refund_requests")


@login_required
def reject_refund_request(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    refund_request = get_object_or_404(RefundRequest, pk=id)
    refund_request.reject()
    return redirect("manage_refund_requests")

@login_required
def new_refund_request(request):
    if request.method == "POST":
        form = RefundRequestForm(request.POST, user=request.user)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.user = request.user
            refund.save()
            return redirect("my_refund_requests")
    else:
        form = RefundRequestForm(user=request.user)

    return render(request, "app/refund/create_refund_request.html", {"form": form})


@login_required
def refund_detail(request, id):
    # Solo organizadores pueden ver cualquier detalle, los usuarios solo los suyos
    refund = get_object_or_404(RefundRequest, pk=id)
    if not request.user.is_organizer and refund.user != request.user:
        return redirect("events")  # o donde quieras  

    return render(
        request,
        "app/refund/refund_detail.html",
        {"refund": refund}
    )

@login_required
def edit_refund_request(request, id):
    refund = get_object_or_404(RefundRequest, pk=id, user=request.user)
    # Solo se edita si está pendiente
    if refund.approved is not None:
        return redirect("my_refund_requests")

    if request.method == "POST":
        form = RefundRequestForm(request.POST, instance=refund, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("my_refund_requests")
    else:
        form = RefundRequestForm(instance=refund, user=request.user)

    return render(request, "app/refund/edit_refund_request.html", {
        "form": form,
        "refund": refund
    })




# ------------------- Tickets -------------------
@login_required
def ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, 'app/ticket/ticket_list.html', {'tickets': tickets})


@login_required
def ticket_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.user = request.user
            ticket.save()
            return redirect('ticket_list')
    else:
        form = TicketForm()

    return render(request, 'app/ticket/ticket_form.html', {
        'form': form,
        'event': event
    })


@login_required
def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('ticket_list')
    else:
        form = TicketForm(instance=ticket)

    return render(request, 'app/ticket/ticket_form.html', {
        'form': form,
        'event': ticket.event
    })


@login_required
def ticket_delete(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        ticket.delete()
        return redirect('ticket_list')
    return render(request, 'app/ticket/ticket_confirm_delete.html', {'ticket': ticket})


# ------------------- Categorías -------------------
@login_required
def categories(request):
    categories = Category.objects.annotate(event_count=Count('events')).order_by("name")
    return render(request, "category/categories.html", {
        "categories": categories,
        "user_is_organizer": request.user.is_organizer,
    })


@login_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)
    return render(request, "category/category_detail.html", {
        "category": category,
        "user_is_organizer": request.user.is_organizer,
    })


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
def category_form(request, id=None):
    user = request.user
    if not user.is_organizer:
        return redirect("categories")

    category = get_object_or_404(Category, pk=id) if id else None

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect("categories")
    else:
        form = CategoryForm(instance=category)

    return render(request, "category/category_form.html", {
        "form": form,
        "category": category,
        "user_is_organizer": request.user.is_organizer,
    })


# ------------------- Notificaciones -------------------
class OrganizerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_organizer # type: ignore


class NotificationList(LoginRequiredMixin, generic.ListView):
    template_name = "notifications/list.html"
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.notifications.all() # type: ignore


class NotificationCreate(OrganizerRequiredMixin, generic.CreateView):
    model = Notification
    form_class = NotificationForm
    template_name = "notifications/form.html"
    success_url = reverse_lazy("notifications_list")


class NotificationUpdate(OrganizerRequiredMixin, generic.UpdateView):
    model = Notification
    form_class = NotificationForm
    template_name = "notifications/form.html"
    success_url = reverse_lazy("notifications_list")


class NotificationDelete(OrganizerRequiredMixin, generic.DeleteView):
    model = Notification
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
        notifs = request.user.notifications.order_by("-created_at")[:5]
        html = render_to_string(
            "notifications/_dropdown_items.html",
            {"notifs": notifs},
            request=request,
        )
        return JsonResponse({"html": html})
