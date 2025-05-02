import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Event, Ticket, User, PaymentInfo
from .forms import EventForm, TicketForm,PaymentForm, TicketFilterForm
from django.core.exceptions import ValidationError
from decimal import Decimal
import qrcode
from io import BytesIO
import qrcode.constants  
from django.db import transaction
from django.db.models import Count, Sum

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
                {"errors": errors, "data": request.POST},
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
    now = timezone.now()
    can_edit = request.user.is_organizer and request.user == event.organizer
    return render(request, "app/event_detail.html", {
        "event": event, 
        "can_edit": can_edit, 
        "now": now
    })

@login_required
def event_delete(request, id):
    if not request.user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")

@login_required
def organizer_tickets(request, event_id=None):
    if not request.user.is_organizer:
        return redirect('events')
    
    if event_id:
      
        event = get_object_or_404(Event, pk=event_id, organizer=request.user)
        tickets = Ticket.objects.filter(event=event).select_related('user').order_by('-buy_date')
        return render(request, 'app/organizer_tickets_event.html', {
            'event': event,
            'tickets': tickets,
            'total_sales': sum(t.total for t in tickets),
            'tickets_count': tickets.count()
        })
    else:
       
        events = Event.objects.filter(organizer=request.user).annotate(
            tickets_sold=Count('ticket'),
            total_sales=Sum('ticket__total')
        ).order_by('-scheduled_at')
        
        return render(request, 'app/organizer_event_list.html', {
            'events': events
        })

@login_required
def event_form(request, id=None):
    if not request.user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            
            scheduled_date = form.cleaned_data.get('scheduled_date')
            scheduled_time = form.cleaned_data.get('scheduled_time')
            
            if scheduled_date and scheduled_time:
                combined_datetime = datetime.datetime.combine(scheduled_date, scheduled_time)
                event.scheduled_at = timezone.make_aware(combined_datetime)
            
            if id is None:
                event.general_tickets_available = event.general_tickets_total
                event.vip_tickets_available = event.vip_tickets_total
            else:
                original_event = get_object_or_404(Event, pk=id)
                general_diff = event.general_tickets_total - original_event.general_tickets_total
                vip_diff = event.vip_tickets_total - original_event.vip_tickets_total
                
                event.general_tickets_available = original_event.general_tickets_available + general_diff
                event.vip_tickets_available = original_event.vip_tickets_available + vip_diff
                
                event.pk = original_event.pk
                event.created_at = original_event.created_at
            
            event.save()
            return redirect("events")
        else:
            return render(
                request,
                "app/event_form.html",
                {"form": form, "event_id": id, "user_is_organizer": request.user.is_organizer}
            )
    else:
        initial_data = {}
        if id is not None:
            event = get_object_or_404(Event, pk=id)
            scheduled_datetime = timezone.localtime(event.scheduled_at)
            initial_data = {
                'title': event.title,
                'description': event.description,
                'general_price': event.general_price,
                'vip_price': event.vip_price,
                'general_tickets_total': event.general_tickets_total,
                'vip_tickets_total': event.vip_tickets_total,
                'scheduled_date': scheduled_datetime.date(),
                'scheduled_time': scheduled_datetime.time()
            }
            form = EventForm(initial=initial_data)
        else:
            form = EventForm()

    return render(
        request,
        "app/event_form.html",
        {"form": form, "event_id": id, "user_is_organizer": request.user.is_organizer},
    )




@login_required
@transaction.atomic
def ticket_purchase(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.user.is_organizer :
        
        return redirect('event_detail', id=event_id)
    
    if request.method == 'POST':
        ticket_form = TicketForm(request.POST, event=event)
        payment_form = PaymentForm(request.POST)
        
        if ticket_form.is_valid() and payment_form.is_valid():
            try:
                with transaction.atomic():
                    ticket = ticket_form.save(commit=False)
                    ticket.user = request.user
                    ticket.event = event
                    ticket.ticket_code = ticket._generate_ticket_code()
                    
                    price = event.general_price if ticket.type == Ticket.TicketType.GENERAL else event.vip_price
                    ticket.subtotal = price * Decimal(ticket.quantity)
                    ticket.taxes = ticket.subtotal * Decimal('0.10')
                    ticket.total = ticket.subtotal + ticket.taxes
                    ticket.payment_confirmed = True
                    
              
                    payment_info = payment_form.save(commit=False)
                    payment_info.user = request.user
                    
                    if payment_form.cleaned_data.get('save_card'):
                        payment_info.save()
                    
                    ticket.save()
                    
                
                    if ticket.type == Ticket.TicketType.GENERAL:
                        event.general_tickets_available -= ticket.quantity
                    else:
                        event.vip_tickets_available -= ticket.quantity
                    event.save()
                    
                    
                    return redirect('ticket_detail', ticket_id=ticket.id)
                    
            except Exception as e:
                
             
                print(f"Error during ticket purchase: {str(e)}")
        else:
            
            print("Ticket form errors:", ticket_form.errors)
            print("Payment form errors:", payment_form.errors)
    else:
        ticket_form = TicketForm(event=event)
        payment_form = PaymentForm()

    return render(request, 'app/ticket_purchase.html', {
        'event': event,
        'ticket_form': ticket_form,
        'payment_form': payment_form,
    })

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    
    if ticket.user != request.user and (not request.user.is_organizer or request.user != ticket.event.organizer):
        return HttpResponseForbidden("No tienes permiso para ver este ticket")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket.ticket_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    qr_code_base64 = ticket.qr_code_base64()
    
    return render(request, 'app/ticket_detail.html', {
        'ticket': ticket,
        'qr_code': qr_code_base64,
        'is_editable': ticket.can_be_modified_by(request.user),
        'is_organizer': request.user.is_organizer and request.user == ticket.event.organizer
    })

@login_required
@transaction.atomic
def ticket_update(request, ticket_id):
    ticket = get_object_or_404(Ticket.objects.select_related('event'), pk=ticket_id)
    
  
    if not ticket.can_be_modified_by(request.user):
        
        return redirect('ticket_detail', ticket_id=ticket_id)
    
   
    if not ticket._is_within_edit_window():
        
        return redirect('ticket_detail', ticket_id=ticket_id)
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket, event=ticket.event)
        if form.is_valid():
            try:
                with transaction.atomic():
                 
                    original_type = ticket.type
                    original_quantity = ticket.quantity
                
                    
                    updated_ticket = form.save(commit=False)
                    
                
                    new_type = updated_ticket.type
                    new_quantity = updated_ticket.quantity
                    
         
                    type_changed = original_type != new_type
                    quantity_diff = new_quantity - original_quantity
                    
                
                    if type_changed or quantity_diff > 0:
                        if type_changed:
                            
                            available = ticket.event.get_available_tickets(new_type)
                            if available < new_quantity:
                                messages.error(request, f"No hay suficientes entradas {new_type.lower()} disponibles")
                                return redirect('ticket_update', ticket_id=ticket_id)
                        else:
                            
                            available = ticket.event.get_available_tickets(new_type)
                            if available < quantity_diff:
                                messages.error(request, f"No hay suficientes entradas {new_type.lower()} disponibles")
                                return redirect('ticket_update', ticket_id=ticket_id)
                    
                    
                    price = ticket.event.general_price if new_type == Ticket.TicketType.GENERAL else ticket.event.vip_price
                    
                    
                    updated_ticket.subtotal = price * Decimal(new_quantity)
                    updated_ticket.taxes = updated_ticket.subtotal * Decimal('0.10')
                    updated_ticket.total = updated_ticket.subtotal + updated_ticket.taxes
                    
                    
                    if type_changed:
                        
                        if original_type == Ticket.TicketType.GENERAL:
                            ticket.event.general_tickets_available += original_quantity
                        else:
                            ticket.event.vip_tickets_available += original_quantity
                            
                        if new_type == Ticket.TicketType.GENERAL:
                            ticket.event.general_tickets_available -= new_quantity
                        else:
                            ticket.event.vip_tickets_available -= new_quantity
                    else:
                       
                        if new_type == Ticket.TicketType.GENERAL:
                            ticket.event.general_tickets_available -= quantity_diff
                        else:
                            ticket.event.vip_tickets_available -= quantity_diff
                    
                    
                    ticket.event.save()
                    
                    
                    updated_ticket.save()
                    
                    messages.success(request, "Ticket actualizado correctamente")
                    return redirect('ticket_detail', ticket_id=ticket_id)
                    
            except Exception as e:
                messages.error(request, f"Error al actualizar el ticket: {str(e)}")
                
                print(f"Error updating ticket: {str(e)}")
                return redirect('ticket_update', ticket_id=ticket_id)
    else:
        form = TicketForm(instance=ticket, event=ticket.event)
    
    return render(request, 'app/ticket_update.html', {
        'form': form,
        'ticket': ticket,
        'now': timezone.now(),
        'original_price': ticket.event.general_price if ticket.type == Ticket.TicketType.GENERAL else ticket.event.vip_price
    })
@login_required
@transaction.atomic
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket.objects.select_related('event', 'user'), pk=ticket_id)
    
 
    if not (ticket.user == request.user or 
            (request.user.is_organizer and request.user == ticket.event.organizer)):
        
        return redirect('ticket_detail', ticket_id=ticket_id)
    

    if request.user.is_organizer and request.user == ticket.event.organizer:
        redirect_url = 'organizer_tickets_event'
        redirect_kwargs = {'event_id': ticket.event.id}
    else:
        redirect_url = 'ticket_list'
        redirect_kwargs = {}

    if request.method == 'POST':
        try:
            with transaction.atomic():
                
                if ticket.type == Ticket.TicketType.GENERAL:
                    ticket.event.general_tickets_available += ticket.quantity
                else:
                    ticket.event.vip_tickets_available += ticket.quantity
                
                ticket.event.save()
                ticket.delete()
                
                
                return redirect(redirect_url, **redirect_kwargs)
                
        except Exception as e:
            messages.error(request, f"Error al eliminar el ticket: {str(e)}")
            return redirect('ticket_detail', ticket_id=ticket_id)
    
    
    return render(request, 'app/ticket_delete.html', {
        'ticket': ticket,
        'is_organizer': request.user.is_organizer and request.user == ticket.event.organizer,
        'redirect_url': redirect_url,
        'redirect_kwargs': redirect_kwargs
    })

@login_required
def ticket_use(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    
    if not request.user.is_organizer or ticket.event.organizer != request.user:
        messages.error(request, "No tienes permiso para marcar este ticket")
        return redirect('event_detail', id=ticket.event.id)
    
    if request.method == 'POST':
        if ticket.is_used:
            messages.warning(request, "Este ticket ya estaba marcado como usado")
        else:
            ticket.is_used = True
            ticket.save()
            messages.success(request, f"Ticket #{ticket.ticket_code} marcado como usado")
    
    return redirect('event_detail', id=ticket.event.id)

@login_required
def ticket_list(request):
    now = timezone.now()
    tickets = Ticket.objects.filter(user=request.user).select_related('event').order_by('-buy_date')
    filter_form = TicketFilterForm(request.GET or None)
    
    if filter_form.is_valid():
        filter_by = filter_form.cleaned_data.get('filter_by', 'all')
        
        if filter_by == 'upcoming':
            tickets = tickets.filter(event__scheduled_at__gt=now)
        elif filter_by == 'past':
            tickets = tickets.filter(event__scheduled_at__lte=now)
        elif filter_by == 'used':
            tickets = tickets.filter(is_used=True)
        elif filter_by == 'unused':
            tickets = tickets.filter(is_used=False)
    
    return render(request, 'app/ticket_list.html', {
        'tickets': tickets,
        'filter_form': filter_form,
        'now': now
    })

def calculate_refund_fee(ticket):
    days_until_event = (ticket.event.scheduled_at - timezone.now()).days
    
    if days_until_event > 7:
        return 0
    elif 3 < days_until_event <= 7:
        return 10
    elif 1 < days_until_event <= 3:
        return 20
    else:
        return 30

def process_payment(card_type, card_number, expiry_month, expiry_year, cvv, card_holder, amount):
    if card_number.endswith('1111'):
        return False, "Tarjeta declinada por el banco emisor"
    
    import random
    if random.random() < 0.05:
        return False, "Error de conexión con el procesador de pagos"
    
    return True, "Pago procesado exitosamente"

def process_refund(ticket, amount):
    import random
    if random.random() < 0.05:
        return False
    
    return True