import datetime
from functools import wraps
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Event, User, Notification, NotificationUser, Category, Ticket, Event, TicketForm
from .validations.notifications import createNotificationValidations
from django.db.models import Count
import math
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Venue
from .forms import VenueForm
from .models import Event, Rating, Rating_Form, User, Comment


def organizer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login') 
        if not request.user.is_organizer:
            return redirect('events')
        return view_func(request, *args, **kwargs)
    return wrapper



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

def verVenues(request):
    venues = Venue.objects.all() 
    return render(request, 'app/venue_list.html', {'venues': venues, "user_is_organizer": request.user.is_organizer})

@login_required
@organizer_required
def crearVenues(request):
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('venue_list')
    else:
        form = VenueForm() 
    return render(request, 'app/venue_form.html', {'form': form, "user_is_organizer": request.user.is_organizer})

@login_required
@organizer_required
def editarVenues(request, pk):
    venue = get_object_or_404(Venue, pk=pk) 
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue) 
        if form.is_valid():
            form.save()  
            return redirect('venue_list') 
    else:
        form = VenueForm(instance=venue)
    return render(request, 'app/venue_form.html', {'form': form, "user_is_organizer": request.user.is_organizer})

@login_required
@organizer_required
def eliminarVenue(request, pk):
    venue = get_object_or_404(Venue, pk=pk) 
    if request.method == 'POST':
        venue.delete() 
        return redirect('venue_list') 
    return render(request, 'app/venue_confirm_delete.html', {'venue': venue, "user_is_organizer": request.user.is_organizer})


@login_required
def categories(request):

    categories = Category.objects.annotate(event_count=Count('events')).order_by('updated_at')

    return render(
        request,
        "app/categories.html",
        {"categories": categories, "user_is_organizer": request.user.is_organizer},
    )

@login_required
@organizer_required
def category_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")

        if id is None:
            Category.new(name, description)
        else:
            category = get_object_or_404(Category, pk=id)
            category.update(name, description)

        return redirect("categories")

    category = {}
    if id is not None:
        category = get_object_or_404(Category, pk=id)

    return render(
        request,
        "app/category_form.html",
        {"category": category, "user_is_organizer": request.user.is_organizer},
    )

@login_required
@organizer_required
def category_edit(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("categories")

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        category = None
        if id is not None:
            category = get_object_or_404(Category, pk=id)

        if category: 
            category.update(name, description)
        return redirect("categories")

    category = None
    if id is not None:
        category = get_object_or_404(Category, pk=id)

    return render(
        request,
        "app/category_form.html",
        {
            "category": category,
            "user_is_organizer": user.is_organizer,
        }
    )

@login_required
@organizer_required
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
@organizer_required
def category_detail(request, id):
    event = get_object_or_404(Category, pk=id)
    return render(request, "app/category_detail.html", {"category": event, "user_is_organizer": request.user.is_organizer})


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def my_events(request):
    if not request.user.is_organizer:
        return redirect("events")
    
    events = Event.objects.filter(organizer=request.user).order_by("scheduled_at")
    return render(
        request,
        "app/my_events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    comments = event.comments.all().order_by("-created_at") # type: ignore
    return render(request, "app/event_detail.html", {"event": event, "user_is_organizer": request.user == event.organizer, "comments": comments})

@login_required
@organizer_required
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
@organizer_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    # Obtener todos los venues disponibles
    venues = Venue.objects.all()

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        category_ids = request.POST.getlist('categories')  # Lista de IDs
        venue_id = request.POST.get("venue")  # Obtener el venue seleccionado

        # Parsear fecha y hora
        year, month, day = date.split("-")
        hour, minutes = time.split(":")
        scheduled_at = timezone.make_aware(
            timezone.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        # Crear o actualizar el evento
        if id is None:
            # Crear evento
            venue = get_object_or_404(Venue, pk=venue_id) if venue_id else Venue.objects.first()
            if venue is None:
                raise ValueError("No se ha proporcionado un lugar de celebración y no se dispone de un lugar de celebración por defecto.")
            success, event_or_errors = Event.new(title, description, scheduled_at, request.user, category_ids, venue)
            if not success:
                errors = event_or_errors
                
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)
            categories = Category.objects.filter(id__in=category_ids)
            event.categories.set(categories)
            venue = get_object_or_404(Venue, pk=venue_id) if venue_id else Venue.objects.first()
            if venue is None:
                raise ValueError("No se ha proporcionado un lugar de celebración y no se dispone de un lugar de celebración por defecto.")
            event.venue = venue
            event.save()

            return redirect('event_detail', id=event.id)

        if success:
            return redirect('event_detail', id=event_or_errors.id)

  
    event = None
    event_categories_ids = []
    event_venue = None
    if id:
        event = get_object_or_404(Event, pk=id)
        event_categories_ids = list(event.categories.values_list('id', flat=True))
        event_venue = event.venue 
    else:
        event = {}

    categories = list(Category.objects.all())

   
    total = len(categories)
    per_column = math.ceil(total / 3)
    categories_chunks = [categories[i:i + per_column] for i in range(0, total, per_column)]

    context = {
        'event': event,
        'categories': categories,
        'categories_chunks': categories_chunks,
        'event_categories_ids': event_categories_ids,
        'user_is_organizer': user.is_organizer,
        'venues': venues, 
        'event_venue': event_venue, 
    }

    return render(request, 'app/event_form.html', context)

@login_required
def notifications(request):
    user = request.user
    
    notifications = Notification.objects.filter(users=user).order_by("-created_at")

    if user.is_organizer:
        return render(
        request,
        "app/notifications_admin.html",
        {"notifications": notifications, "user_is_organizer": request.user.is_organizer})        

    for notification in notifications:
        link = NotificationUser.objects.filter(notification=notification, user=user).first()
        setattr(notification, 'is_read', link.is_read if link else True)
    
    new_notifications_count = Notification.objects.filter(
        notificationuser__is_read=False, 
        notificationuser__user=user).count()

    return render(
        request,
        "app/notifications.html",
        {
            "notifications": notifications,
            "new_notifications_count": new_notifications_count
        },
    )

###################################################################################

@login_required
def comments(request):
    if not request.user.is_organizer:
        return redirect("events")

    comments = Comment.objects.filter(event__organizer=request.user).order_by("-created_at")
    return render(
        request,
        "app/comments/comments.html",
        {"comments": comments, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def comment_list(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    comments = Comment.objects.filter(event=event).order_by('-created_at')
    return render(
        request,
        "app/comments/comment_list.html",
        {"comments": comments, "user": request.user, "user_is_organizer": request.user == event.organizer, "event": event}
    )
 

@login_required
def comment_detail(request, comment_id):
    if not request.user.is_organizer:
        return redirect("events")
    comment = get_object_or_404(Comment, pk=comment_id)
    return render(request, "app/comments/comment_detail.html", {"comment": comment})


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.user != request.user and comment.event.organizer != request.user:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    if request.method == "POST":
        next_url = request.POST.get("next")
        comment.delete()
        return redirect(next_url)

    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def comment_form(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")

        success, result = Comment.new(title, text, request.user, event)

        if success:
            return redirect("event_detail", id=event_id)
        else:
            return render(
                request,
                "app/event_detail.html",{
                    "errors": result,
                    "event": event,
                    "comment": {
                        "title": title,
                        "text": text
                },
                "comments": event.comments.all() # type: ignore
                }
            )
        
    return redirect("event_detail", id=event_id)

@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.user != request.user and comment.event.organizer != request.user:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        next_url = request.POST.get("next")
        
        success, result = comment.update(title, text)

        if success:
            if next_url:
                return redirect(next_url)
            
            if comment.user == comment.event.organizer:
                return redirect("comments")
            else:
                return redirect("event_detail", id=comment.event.pk)
        else:
            return render(request, "app/comments/comment_edit.html", {
                "comment": {
                    "id": comment.pk,
                    "title": title,
                    "text": text,
                    "user": comment.user,
                    "event": comment.event
                },
                "errors": result,
                "next_url": next_url
            })
    
    next_url = request.GET.get("next", "/")
    return render(request, "app/comments/comment_edit.html", {
        "comment": comment,
        "next_url": next_url
    })

@login_required
def buy_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.event = event
            ticket.save()
            messages.success(request, f'¡Ticket comprado con éxito! Tu código es: {ticket.ticket_code}')
            return redirect('ticket_detail', ticket_id=ticket.id)
        
    else:
        form = TicketForm()
    
    return render(request, 'app/buy_ticket.html', {
        'form': form,
        'event': event,
        "user_is_organizer": request.user.is_organizer
    })

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.user != ticket.user and not (request.user.is_organizer and request.user == ticket.event.organizer):
        messages.error(request, 'No tienes permiso para ver este ticket')
        return redirect('home')
    
    return render(request, 'app/ticket_detail.html', {'ticket': ticket, "user_is_organizer": request.user.is_organizer})

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    if request.user != ticket.user:
        messages.error(request, 'No tienes permiso para editar este ticket')
        return redirect('home')
    
    
    time_difference = timezone.now() - ticket.buy_date
    if time_difference.total_seconds() > 1800:
        messages.error(request, 'Solo puedes editar el ticket dentro de los primeros 30 minutos después de la compra')
        return redirect('ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ticket actualizado con éxito')
            return redirect('ticket_detail', ticket_id=ticket.id)
    else:
        form = TicketForm(instance=ticket)
    
    return render(request, 'app/edit_ticket.html', {
        'form': form,
        'ticket': ticket
    })

@login_required
def delete_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.user != ticket.user and not (request.user.is_organizer and request.user == ticket.event.organizer):
        messages.error(request, 'No tienes permiso para eliminar este ticket')
        return redirect('home')
    
    if request.user == ticket.user:
        time_difference = timezone.now() - ticket.buy_date
        if time_difference.total_seconds() > 1800:
            messages.error(request, 'Solo puedes eliminar el ticket dentro de los primeros 30 minutos después de la compra')
            return redirect('ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Ticket eliminado con éxito')
        return redirect('my_tickets')
    
    return render(request, 'app/delete_ticket.html', {'ticket': ticket})

@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user).order_by('-buy_date')
    return render(request, 'app/my_tickets.html', {'tickets': tickets, "user_is_organizer": request.user.is_organizer})

@organizer_required
def notification_detail(request, id):
    notification = get_object_or_404(Notification, pk=id)
    return render(request, "app/notification_detail.html", {"notification": notification})

@login_required
@organizer_required
def notification_edit(request, id):
    notification = get_object_or_404(Notification, pk=id)
    events = Event.objects.all().order_by("scheduled_at")
    users = User.objects.filter(is_organizer = False)
    errors = {}

    if request.method == "POST":
        user_id = request.POST.get("user")
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        event_id = request.POST.get("event")
        event = get_object_or_404(Event, id=event_id)
        recipient_type = request.POST.get("recipient_type")

        users = []
        if recipient_type == "all_users":
            users = User.objects.all()
        else:
            user = get_object_or_404(User, id=user_id)
            users.append(user)
        
        validations_pass, errors = createNotificationValidations(users, event, title, message, priority)
        if validations_pass == False:
            return render(
                request,
                "app/notification_form.html",
                {
                    "notification": { title, message, priority }, 
                    "events": events, 
                    "users": users,
                    "errors": errors
                },
            )
        
        notification = get_object_or_404(Notification, pk=id)
        notification.update(users, event, title, message, priority)

        return redirect("notifications")

    return render(
        request,
        "app/notification_form.html",
        {
            "notification": notification, 
            "events": events, 
            "users": users,
            "errors": errors
        },
    )
    
@login_required
@organizer_required
def notification_delete(request, id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, pk=id)
        notification.delete()

    return redirect("notifications")

@login_required
@organizer_required
def notification_form(request):
    notification = {}
    errors = {}
    events = Event.objects.all().order_by("scheduled_at")
    users = User.objects.filter(is_organizer = False)

    if request.method == "POST":
        user_id = request.POST.get("user")
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        event_id = request.POST.get("event")
        event = get_object_or_404(Event, id=event_id)
        recipient_type = request.POST.get("recipient_type")

        users = []
        if recipient_type == "all_users":
            users = User.objects.all()
        else:
            user = get_object_or_404(User, id=user_id)
            users.append(user)
        
        validations_pass, errors = createNotificationValidations(users, event, title, message, priority)
        if validations_pass == False:
            return render(
                request,
                "app/notification_form.html",
                {
                    "notification": { title, message, priority }, 
                    "events": events, 
                    "users": users,
                    "errors": errors
                },
            )
        
        Notification.new(users, event, title, message, priority)

        return redirect("notifications")
        
    return render(
        request,
        "app/notification_form.html",
        {
            "notification": notification, 
            "events": events, 
            "users": users,
            "errors": errors
        },
    )
    
def mark_all_as_read(request):
    user = request.user

    NotificationUser.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)

    return redirect("notifications")

def mark_as_read(request, id):
    user = request.user
    notification = get_object_or_404(Notification, pk=id)
    notification.mark_as_read(user.id)

    return redirect("notifications")

@login_required
def event_rating(request, id):
    evento = get_object_or_404(Event, pk=id)
    resenas = Rating.objects.filter(evento=evento)
    cantidad_resenas = resenas.count()

    try:
        resena_existente = Rating.objects.get(usuario=request.user, evento=evento)
        editando = True
    except Rating.DoesNotExist:
        resena_existente = None
        editando = False
        
    if request.method == 'POST':
        if 'guardar' in request.POST:
            form = Rating_Form(request.POST, instance=resena_existente)
            if form.is_valid():
                nueva_resena = form.save(commit=False)
                nueva_resena.usuario = request.user 
                nueva_resena.evento = evento
                nueva_resena.save()
                messages.success(request, "¡Tu reseña fue guardada exitosamente!")
            return redirect('event_rating', id=evento.id) # type: ignore
        
        elif 'eliminar' in request.POST and resena_existente:
            resena_existente.delete()
            messages.success(request, "¡Tu reseña fue eliminada exitosamente!")
            return redirect('event_rating', id=evento.id) # type: ignore

        elif 'cancelar' in request.POST:
            form = Rating_Form()
            return redirect('event_rating', id=evento.id) #type: ignore

    form = Rating_Form(instance=resena_existente)            
        
    return render(request, 'app/event_rating.html', {
        'evento': evento,
        'ratings' : resenas,
        'form': form,
        'editando': editando,
        'cantidad_resenas': cantidad_resenas
    })
