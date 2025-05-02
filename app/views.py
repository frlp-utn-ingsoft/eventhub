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
from django.db import transaction
from django.db.models import Q
from .utils import format_datetime_es


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
    # Usuario autenticado → redirigimos a su página principal (events)
    if request.user.is_authenticated:
        return redirect("events")          # o "home_organizer" / "home_user" más adelante

    # Visitante → página pública
    return render(request, "home_guest.html")

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


@login_required
def notifications_list(request):
    query = request.GET.get("q", "")
    filter_event = request.GET.get("event")
    filter_priority = request.GET.get("priority")

    tickets_user_events = Event.objects.filter(tickets__user=request.user).distinct()

    received_notifications = Notification.objects.filter(
        Q(user=request.user) |
        Q(to_all_event_attendees=True, event__in=tickets_user_events)
    ).distinct()

    if query:
        received_notifications = received_notifications.filter(title__icontains=query)
    if filter_event:
        received_notifications = received_notifications.filter(event__id=filter_event)
    if filter_priority:
        received_notifications = received_notifications.filter(priority=filter_priority)

    # Agregar fecha formateada
    for notif in received_notifications:
        notif.formatted_date = format_datetime_es(notif.created_at)

    sent_notifications = None
    if hasattr(request.user, 'is_organizer') and request.user.is_organizer:
        sent_notifications = Notification.objects.filter(created_by=request.user)
        if query:
            sent_notifications = sent_notifications.filter(title__icontains=query)
        if filter_event:
            sent_notifications = sent_notifications.filter(event__id=filter_event)
        if filter_priority:
            sent_notifications = sent_notifications.filter(priority=filter_priority)

        for notif in sent_notifications:
            notif.formatted_date = format_datetime_es(notif.created_at)

    all_events = tickets_user_events

    return render(request, "notifications/notifications_list.html", {
        "received_notifications": received_notifications,
        "sent_notifications": sent_notifications,
        "all_events": all_events,
        "filter_event": filter_event,
        "filter_priority": filter_priority,
        "query": query,
    })
@login_required
def create_notification(request):
    if not request.user.is_organizer:
        return redirect('home')

    if request.method == 'POST':
        form = NotificationForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    target = form.cleaned_data['target']
                    title = form.cleaned_data['title']
                    message = form.cleaned_data['message']
                    priority = form.cleaned_data['priority']
                    to_all = form.cleaned_data['to_all_event_attendees']
                    event = form.cleaned_data.get('event')
                    user = form.cleaned_data.get('user')

                    if target == 'event' and event:
                        Notification.objects.create(
                            event=event,
                            to_all_event_attendees=True,
                            title=title,
                            message=message,
                            priority=priority,
                            created_by=request.user
                        )
                    elif target == 'user' and user:
                        Notification.objects.create(
                            user=user,
                            to_all_event_attendees=False,
                            title=title,
                            message=message,
                            priority=priority,
                            created_by=request.user
                        )
                    else:
                        raise Exception("Destino no válido en el formulario.")
            except Exception as e:
                form.add_error(None, f"Ocurrió un error al crear notificaciones: {e}")
            else:
                return redirect('notifications_list')
    else:
        form = NotificationForm(user=request.user)

    return render(request, 'notifications/create_notification.html', {'form': form})

@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)

    # El usuario tiene acceso si:
    # - es el destinatario directo
    # - o es el creador (organizador)
    # - o es destinatario masivo y tiene ticket para ese evento
    user = request.user
    tiene_ticket = notification.event and notification.event.tickets.filter(user=user).exists()

    if not (
        notification.user == user or
        notification.created_by == user or
        (notification.to_all_event_attendees and tiene_ticket)
    ):
        return redirect("notifications_list")

    # Formatear fecha en español
    notification.formatted_date = format_datetime_es(notification.created_at)

    return render(request, "notifications/notifications_detail.html", {
        "notification": notification
    })

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
        # Obtener eventos del usuario
        user_events = Event.objects.filter(tickets__user=request.user)

        notif = get_object_or_404(
            Notification,
            Q(user=request.user) | Q(to_all_event_attendees=True, event__in=user_events),
            pk=pk
        )
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return redirect("notifications_list")


class NotificationDropdown(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        events = Event.objects.filter(tickets__user=user).distinct()

        notifs = Notification.objects.filter(
            Q(user=user) |
            Q(to_all_event_attendees=True, event__in=events)
        ).order_by("-created_at").distinct()[:5]

        html = render_to_string(
            "notifications/_dropdown_items.html",
            {"notifs": notifs},
            request=request,
        )
        return JsonResponse({"html": html})
