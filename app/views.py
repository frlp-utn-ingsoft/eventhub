import datetime
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.db.models import Count

from django.core.exceptions import ValidationError
from django.urls import reverse


from django.http import HttpResponseForbidden, HttpResponseNotAllowed

from .forms import CategoryForm, CommentForm, EventForm, RefundRequestForm
from .models import Category, Comment, Event, RefundRequest, Ticket, User, Venue, Notification
from django.http import JsonResponse

def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(
            email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "app/accounts/register.html",
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
            return redirect("home")

    return render(request, "app/accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "app/accounts/login.html", {
                    "error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("home")

    return render(request, "app/accounts/login.html")


def home(request):
    user = request.user

    user_is_organizer = False
    if user.is_authenticated:
        user_is_organizer = user.is_organizer

    context = {
        "user_is_organizer": user_is_organizer,
    }
    return render(request, "home.html", context)


@login_required
def event(request):
    queryset = Event.objects.all().order_by("scheduled_at")
    favorite_events = request.user.favorites.all() if request.user.is_authenticated else []
    if not request.user.is_organizer:
        queryset = queryset.filter(scheduled_at__gte=timezone.now())
    return render(request, "app/event/events.html", {"events": queryset,
        "user_is_organizer": request.user.is_organizer, "favorite_events": favorite_events})


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, id=id)
    event.update_status()
    comments = Comment.objects.filter(event=event).order_by('-created_at')
    disponibles = (event.venue.capacity if event.venue else 0) - event.tickets_sold
    es_favorito = request.user.favoritos.filter(pk=event.id).exists()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user
            comment.save()
            return redirect('event_detail', id=event.id)
    else:
        form = CommentForm()

    return render(request, 'app/event/event_detail.html', {
        'event': event,
        'comments': comments,
        'form': form,
        'disponibles': max(disponibles, 0),
        'es_favorito': es_favorito,
        'tickets_vendidos': event.tickets_sold,  # <-- aquí
    })


@login_required
def event_delete(request, id):
    if not request.user.is_organizer:
        messages.error(request, "No tienes permisos")
        return redirect("events")

    event = get_object_or_404(Event, pk=id)
    if request.method == "POST":
        event.delete()
        messages.success(request, "Evento eliminado")
        return redirect("events")

    return redirect("events")   


@login_required
def event_form(request, id=None):
    if not request.user.is_organizer:
        messages.error(request, "No tienes permisos")
        return redirect("events")
    
    event = get_object_or_404(Event, pk=id) if id else None
    all_categories = Category.objects.all()
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            form.save_m2m()  
            return redirect('events')
    else:
        form = EventForm(instance=event, user=request.user)

    return render(request, 'app/event/event_form.html', {
        'form': form,
        'categories': all_categories, 
        'event': event,
        'user_is_organizer': request.user.is_organizer 
    })


@login_required
def venue_list(request):
    if not request.user.is_organizer:
        return redirect('events')
    venues = Venue.objects.filter(created_by=request.user)
    return render(request, 'app/venue/venue_list.html', {
        'venues': venues,
        'user_is_organizer': request.user.is_organizer
    })


def venue_form(request, id=None):
    if not request.user.is_organizer:
        return redirect('events')
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact_info = request.POST.get('contact_info')

        if id:
            venue = get_object_or_404(Venue, pk=id)
            venue.update(
                name=name,
                address=address,
                city=city,
                capacity=capacity,
                contact_info=contact_info
            )
        else:
            success, errors = Venue.new(
                name=name,
                address=address,
                city=city,
                capacity=capacity,
                contact_info=contact_info,
                created_by=request.user
            )

            if not success:
                return render(request, 'app/venue_form.html', {
                    'errors': errors,
                    'venue_data': request.POST
                })

        return redirect('venue_list')

    venue = {}
    if id:
        venue = get_object_or_404(Venue, pk=id)

    return render(request, 'app/venue/venue_form.html', {'venue': venue})


@login_required
def venue_delete(request, id):
    if not request.user.is_organizer:
        return redirect('events')

    venue = get_object_or_404(Venue, pk=id)
    if request.method == 'POST':
        venue.delete()
    return redirect('app/venue/venue_list')


class CategoryListView(generic.ListView):
    model = Category
    template_name = 'app/category/category_list.html'


class CategoryCreateView(generic.CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'app/category/category_form.html'
    success_url = reverse_lazy('category_list')

class CategoryUpdateView(generic.UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'app/category/category_form.html'
    success_url = reverse_lazy('category_list')


class CategoryDeleteView(generic.DeleteView):
    model = Category
    template_name = 'app/category/category_confirm_delete.html'
    success_url = reverse_lazy('category_list')


@login_required
def comentarios_organizador(request):
    # Comentarios solo de eventos que creó el organizador actual
    comentarios = Comment.objects.all()

    return render(request, 'app/comments/comentarios_organizador.html', {
        'comentarios': comentarios
    })


def editar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comment, pk=comentario_id)

    if request.method == 'POST':
        if request.user != comentario.user:
            return HttpResponseForbidden()

        comentario.content = request.POST.get('content')
        comentario.save()
        return redirect('comentarios_organizador')


    
@login_required
def eliminar_comentario(request, comentario_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    comentario = get_object_or_404(Comment, pk=comentario_id)
    user = request.user

    es_dueño = (comentario.user == user)

    # Verificamos si el usuario es organizador Y si es dueño del evento asociado al comentario
    try:
        es_organizador_y_dueño_evento = (
            user.is_organizer and comentario.event.organizer == user
        )
    except AttributeError:
        es_organizador_y_dueño_evento = False  # Si no se puede acceder al organizer, no tiene permiso

    if es_dueño or es_organizador_y_dueño_evento:
        comentario.delete()
        messages.success(request, "Comentario eliminado exitosamente.")
        return redirect('comentarios_organizador')
    else:
        return HttpResponseForbidden("No tenés permiso para eliminar este comentario.")




class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'app/tickets/ticket_list.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if getattr(user, "is_organizer", False):
            return qs.filter(event__organizer=user)

        return qs.filter(user=user)
    
class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    template_name = 'app/tickets/ticket_form.html'
    fields = ['event', 'quantity', 'type']
    success_url = reverse_lazy('ticket_list')

    def get_initial(self):
        initial = super().get_initial()
        event_id = self.request.GET.get('event')
        if event_id:
            initial['event'] = event_id
        return initial


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['precio_base_general'] = 50.00  # Precio hardcodeado
        context['precio_base_vip'] = 100.00     # Precio hardcodeado
        event_id =self.request.GET.get('event')
        
        if event_id:
            try:
                context['selected_event'] = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                pass
        return context

    def form_valid(self, form):
        # Calcular precio según el tipo
        event = form.cleaned_data['event']
        quantity = form.cleaned_data['quantity']

        if event.available_tickets == 0:
            messages.error(self.request, "Lo sentimos, las entradas para este evento están agotadas.")
            return redirect('ticket_form')

        if quantity > event.available_tickets:
            form.add_error('quantity', f"Solo quedan {event.available_tickets} entradas disponibles.")
            return self.form_invalid(form)

        is_valid, error_msgs = Ticket.validate_ticket_purchase(
            user=self.request.user,
            event=form.cleaned_data['event'],
            quantity=form.cleaned_data['quantity']
        )
        
        if not is_valid:
            for error in error_msgs:
                form.add_error('quantity', error) 
            return self.form_invalid(form)
            


        # Cálculo de precio 
        if form.cleaned_data['type'] == 'VIP':
            precio_unitario = 100.00
        else:
            precio_unitario = 50.00

        form.instance.user = self.request.user
        form.instance.price_paid = precio_unitario * quantity
        
        response = super().form_valid(form)

        
        # Actualizar tickets vendidos y estado del evento
        event.tickets_sold += quantity
        event.save()
        event.update_status()  # Método existente en el modelo Event

        event.update_availability() 

        return response

class TicketUpdateView(LoginRequiredMixin, UpdateView):
    model = Ticket
    template_name = 'app/tickets/ticket_form.html'
    fields = ['event', 'quantity', 'type']
    success_url = reverse_lazy('ticket_list')

class TicketDeleteView(LoginRequiredMixin, DeleteView):
    model = Ticket
    template_name = 'app/tickets/ticket_confirm_delete.html'
    success_url = reverse_lazy('ticket_list')

@login_required
def update_refund_status(request, refund_id, action):
    """Unifica aprobación y rechazo en una sola vista"""
    refund = get_object_or_404(RefundRequest, id=refund_id)
    
    is_organizer = request.user.is_organizer
    is_own_event = refund.ticket.event.organizer == request.user
    
    if is_organizer and is_own_event:
        if action == 'approve':
            refund.status = 'approved'
            msg_type = messages.success
            msg_text = f"Reembolso #{refund_id} aprobado ✅"
        elif action == 'reject':
            refund.status = 'rejected'
            msg_type = messages.error
            msg_text = f"Reembolso #{refund_id} rechazado ❌"
        else:
            return redirect('manage_refunds')
        
        refund.save()
        msg_type(request, msg_text)
    
    return redirect('manage_refunds')


@login_required
def manage_refunds(request):
    if not request.user.is_organizer:
        return redirect('home')
    

    base_refunds = RefundRequest.objects.filter(
        ticket__event__organizer=request.user
    ).select_related('ticket__event', 'user')
    
    status_counts = {
        'pending': base_refunds.filter(status='pending').count(),
        'approved': base_refunds.filter(status='approved').count(),
        'rejected': base_refunds.filter(status='rejected').count(),
    }
    
    status_filter = request.GET.get('status')
    if status_filter in ['approved', 'rejected', 'pending']:
        refunds = base_refunds.filter(status=status_filter)
    else:
        refunds = base_refunds
    
    return render(request, 'app/refunds/manage.html', {
        'refunds': refunds,
        'status_counts': status_counts,
    })


@login_required
def refund_detail(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    

    if not (request.user == refund.user or request.user.is_organizer):
        return redirect('home')
    
    return render(request, 'app/refunds/detail.html', {
        'refund': refund,
        'can_edit': request.user.is_organizer
    })

@login_required
def request_refund(request):
    if request.method == 'POST':
        ticket_code = request.POST.get('ticket_code')
        try:
            ticket = Ticket.objects.get(
                ticket_code__iexact=ticket_code,
                user=request.user
            )
        except Ticket.DoesNotExist:
            messages.error(request, "❌ Ticket no encontrado o no pertenece a tu cuenta")
            return redirect('request_refund')
        
        tiempo_restante = ticket.event.scheduled_at - timezone.now()
        if tiempo_restante < timedelta(hours=48):
            messages.error(request, "⚠️ No se permiten reembolsos a menos de 48 horas del evento")
            return redirect('request_refund')

        form = RefundRequestForm(request.POST)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.ticket = ticket
            refund.user = request.user
            refund.calcular_monto()
            refund.save()
            messages.success(request, "✅ Solicitud creada exitosamente")
            return redirect('manage_refunds')
    else:
        form = RefundRequestForm()

    return render(request, 'app/refunds/request.html', {
        'form': form,
        'policy_message': "Puedes solicitar reembolsos hasta 48 horas antes del evento."
    })





@login_required
def agregar_favorito(request, event_id):
    evento = get_object_or_404(Event, pk=event_id)
    
    
    if not request.user.favoritos.filter(pk=evento.id).exists():
        request.user.favoritos.add(evento)
        messages.success(request, f"'{evento.title}' añadido a favoritos")
    else:
        messages.info(request, f"'{evento.title}' ya está en tus favoritos")
    
    
    return redirect(request.META.get('HTTP_REFERER', 'lista_favoritos'))

@login_required
def eliminar_favorito(request, event_id):
    evento = get_object_or_404(Event, pk=event_id)
    request.user.favoritos.remove(evento)
    messages.success(request, f"'{evento.title}' eliminado de favoritos")
    return redirect(request.META.get('HTTP_REFERER', 'lista_favoritos'))

@login_required
def lista_favoritos(request):
    favoritos = request.user.favoritos.all().order_by('-scheduled_at')
    return render(request, 'app/event/favoritos/lista.html', {
        'favoritos': favoritos
    })


@login_required
def events(request):
    queryset = Event.objects.all().order_by("scheduled_at")
    if not request.user.is_organizer:
        queryset = queryset.filter(scheduled_at__gte=timezone.now())
    
    # Obtener IDs de eventos favoritos para marcar en template
    favoritos_ids = request.user.favoritos.values_list('id', flat=True)
    
    return render(request, "app/event/events.html", {
        "events": queryset,
        "favoritos_ids": favoritos_ids
    })


@login_required
def notifications(request):
    """Lista todas las notificaciones del usuario"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(read=False).count()
    
    return render(request, 'app/notifications/list_notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    """Marca una notificación como leída"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    if not notification.read:
        notification.read = True
        notification.save()
    return redirect('notifications')

@login_required
def mark_all_notifications_read(request):
    """Marca todas las notificaciones como leídas"""
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect('notifications')

# Agrega este contexto a tus vistas existentes para mostrar el contador
def base_context(request):
    """Contexto común para todas las vistas"""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user, 
            read=False
        ).count()
        return {'unread_notifications_count': unread_count}
    return {}