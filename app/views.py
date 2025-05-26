import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, Ticket, Comment, Notification, Venue
from django.contrib import messages
from django.db.models import Q
import uuid


from .models import Event, User, Ticket, RefundRequest, Rating, Category


def is_organizer(user):
    return user.is_organizer


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
    for ev in events:
        ev.auto_update_state()  # Actualizar el estado de cada evento
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user_has_rated = False
    
    if request.user.is_authenticated:
        user_has_rated = event.ratings.filter(user=request.user).exists()
    
    return render(
        request,
        "app/event_detail.html",
        {
            "event": event,
            "user_is_organizer": request.user.is_organizer,
            "user_has_rated": user_has_rated
        },
    )


@login_required
def event_delete(request, event_id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=event_id)
        event.delete()
        return redirect("events")

    return redirect("events")

@login_required
def event_canceled(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=event_id)
        event.state = Event.CANCELED
        event.save()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, event_id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    categories = Category.objects.filter(is_active=True)
    
    venues = Venue.objects.all()
    event_categories = []
    event = {}

    if event_id is not None:
        event = get_object_or_404(Event, pk=event_id)
        event_categories = [category.id for category in event.categories.all()]

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        
        venue_id = request.POST.get("venue")
        date = request.POST.get("date")
        time = request.POST.get("time")
        categories = request.POST.getlist("categories")
        venue = request.POST.getlist("venue")


        venue = get_object_or_404(Venue, pk=venue_id)
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if event_id is None:
            event = Event.objects.create(
                title=title,
                description=description,
                scheduled_at=scheduled_at,
                organizer=request.user,
                venue=venue
            )
            if categories:
                event.categories.set(categories)
        else:
            event = get_object_or_404(Event, pk=event_id)
            #Marco como reprogamado el evento
            if scheduled_at != event.scheduled_at:
                event.state = Event.REPROGRAMED
            event.title = title
            event.description = description
            event.scheduled_at = scheduled_at
            event.venue = venue
            event.save()
            if categories:
                event.categories.set(categories)

        return redirect("events")

    return render(
        request,
        "app/event_form.html",
        {
            "event": event,
            "categories": categories,
            
            "venues": venues,
            "event_categories": event_categories,
            "user_is_organizer": request.user.is_organizer
        },
    )


@login_required
def refund_form(request, id):
    ticket = get_object_or_404(Ticket, pk=id)

    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        additional_details = request.POST.get("additional_details")
        accepted_policy = request.POST.get("accepted_policy") == "on"

        # Validaciones básicas
        if not ticket_code or not reason or not accepted_policy:
            return render(request, "app/refund_form.html", {
                "error": "Todos los campos son obligatorios.",
                "data": request.POST
            })
        
        #Validacion para evitar que haya solicitudes de reembolso duplicadas
        existing_request = RefundRequest.objects.filter(
            user=request.user,
            approval__isnull=True,  # Reembolso todavia pendientes
        ).first()

        if existing_request:
            return render(request, "app/refund_form.html",{
                "error": "Ya tienes una solicitud de reembolso pendiente.",
                "data": request.POST
            })

        # Crear la solicitud de reembolso con estado pendiente
        RefundRequest.objects.create(
            ticket_code=ticket_code,
            reason=reason,
            additional_details=additional_details,
            user=request.user,
            accepted_policy=accepted_policy,
            approval=None,  # Estado pendiente
            event_name=ticket.event.title
        )

        # Crear una notificación para el usuario que solicitó el reembolso
        notification = Notification.objects.create(
            title="Solicitud de Reembolso Enviada",
            message=f"Tu solicitud de reembolso para el evento: '{ticket.event.title}' ha sido enviada y está en proceso de revisión.",
            priority="MEDIUM",
            event=ticket.event
        )
        notification.users.add(request.user)
        notification.save()

        return redirect("events")

    return render(request, "app/refund_form.html", {"ticket": ticket})


@login_required
def refund_edit_form(request, id):
    refund_request = get_object_or_404(RefundRequest, pk=id)

    
    if request.method == "POST":
        ticket_code_uuid = uuid.UUID(refund_request.ticket_code)
        ticket = Ticket.objects.get(ticket_code=ticket_code_uuid, user=refund_request.user)

        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        additional_details = request.POST.get("additional_details")
        accepted_policy = request.POST.get("accepted_policy") == "on"

        # Validaciones básicas
        if not ticket_code or not reason or not accepted_policy:
            return render(request, "app/refund_form.html", {
                "error": "Todos los campos son obligatorios.",
                "data": request.POST
            })

        # Crear la solicitud de reembolso con estado pendiente
        RefundRequest.objects.update(
            ticket_code=ticket_code,
            reason=reason,
            additional_details=additional_details,
            user=request.user,
            accepted_policy=accepted_policy,
            approval=None,  # Estado pendiente
            event_name=ticket.event.title
        )

        # Crear una notificación para el usuario que solicitó el reembolso
        notification = Notification.objects.create(
            title="Solicitud de Reembolso Enviada",
            message=f"Tu solicitud de reembolso para el evento: '{ticket.event.title}' ha sido enviada y está en proceso de revisión.",
            priority="MEDIUM",
            event=ticket.event
        )
        notification.users.add(request.user)
        notification.save()

        return redirect("events")

    return render(request, "app/refund_edit_form.html", {"refund_request": refund_request})

@login_required
def organizer_refund_requests(request):
    # Si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        # Obtener todos los eventos organizados por el usuario
        refund_requests = RefundRequest.objects.filter(user=request.user)

        # Asignar el evento relacionado a cada refund request
        for r in refund_requests:
            try:
                ticket_code_uuid = uuid.UUID(r.ticket_code)
                ticket = Ticket.objects.get(ticket_code=ticket_code_uuid, user=r.user)
                r.event = ticket.event
            except (Ticket.DoesNotExist, ValueError, TypeError):
                r.event = None

        return render(
            request,
            "app/organizer_refund_requests.html", 
            {
                "refund_requests": refund_requests,
            })
    else:
        # Obtener todos los eventos organizados por el usuario
        organizer_events = Event.objects.filter(organizer=request.user)

        # Obtener todos los refund requests cuyos usuarios compraron tickets para esos eventos
        refund_requests = RefundRequest.objects.filter(
            Q(event_name__in=organizer_events.values_list("title", flat=True))
            ).select_related("user")

        # Asignar el evento relacionado a cada refund request
        for r in refund_requests:
            try:
                ticket_code_uuid = uuid.UUID(r.ticket_code)
                ticket = Ticket.objects.get(ticket_code=ticket_code_uuid, user=r.user)
                r.event = ticket.event
            except (Ticket.DoesNotExist, ValueError, TypeError):
                r.event = None

        return render(request, "app/organizer_refund_requests.html", {
            "refund_requests": refund_requests,
        })


@login_required
def approve_refund_request(request, id):
    if not request.user.is_organizer:
        return redirect("events")

    refund = get_object_or_404(RefundRequest, pk=id)

    # Aseguramos que la solicitud aún no fue procesada
    if refund.approval is not None:
        messages.info(request, "La solicitud ya fue procesada.")
        return redirect("organizer_refund")

    # Buscar el ticket relacionado
    ticket = Ticket.objects.filter(
        ticket_code=refund.ticket_code,
        event__organizer=request.user
    ).first()

    if ticket:
        # Eliminar solo el ticket
        ticket.delete()

    # NO eliminar la refund request, solo actualizarla
    refund.approval = True
    refund.approval_date = timezone.now()
    refund.save()

    return redirect("organizer_refund")


@login_required
def reject_refund_request(request, id):
    # Si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        return redirect("events")
    
    refund = get_object_or_404(RefundRequest, pk=id)
    # Cambiar el estado a rechazado
    refund.approval = False
    refund.approval_date = timezone.now()
    refund.save()
    return redirect("organizer_refund")

@login_required
def refund_delete(request, id):
    
    refund = get_object_or_404(RefundRequest, pk=id)
    # Cambiar el estado a rechazado
    refund.delete()
    
    return redirect("organizer_refund")

@login_required
def view_refund_request(request, id):
    # si no es organizador, redirigir a eventos
    if not request.user.is_organizer:
        return redirect("events")
    refund = get_object_or_404(RefundRequest, pk=id)
    #verificar si la solicitud de reembolso ya fue aprobada o rechazada
    return render(request, "app/view_refund_request.html", {"refund": refund})

@login_required
def buy_ticket(request, id):
    event = get_object_or_404(Event, pk=id)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity"))
        except (TypeError, ValueError):
            messages.error(request, "La cantidad debe ser un número entero")
            return render(request, "app/buy_ticket.html", {"event": event})

        type = request.POST.get("type")
        user = request.user

        success, result = Ticket.new(quantity=quantity, type=type, event=event, user=user)

        if success:
            #GENERO UN CHEQUEO PARA VERIFICAR EL ESTADO DE SOLD OUT
            event.auto_update_state()
            messages.success(request, "¡Ticket comprado!")
            return redirect("tickets")
        else:
            messages.error(request, "Error al comprar el ticket")
            return render(
                request,
                "app/buy_ticket.html",
                {
                    "event": event,
                    "errors": result,
                    "data": request.POST,
                }
            )

    return render(request, "app/buy_ticket.html", {"event": event})

@login_required
def tickets(request):
    user = request.user

    return render(request, "app/tickets.html", {"tickets": user.tickets.all()})

@login_required
def ticket_detail(request, id):
    ticket = get_object_or_404(Ticket, pk=id)

    return render(request, "app/ticket_detail.html", {"ticket": ticket})

@login_required
def ticket_delete(request, id):
    user = request.user

    if request.method == "POST":
        ticket = get_object_or_404(Ticket, pk=id)

        if (ticket.user == user):
            ticket.delete()

    return redirect("tickets")

@login_required
def ticket_edit(request, id):
    ticket = get_object_or_404(Ticket, pk=id)

    if request.method == "POST":
        print ("Entraste al POST")
        try:
            quantity = int(request.POST.get("quantity"))
        except (TypeError, ValueError):
            messages.error(request, "La cantidad debe ser un número entero")
            return render(request, "app/buy_ticket.html", {"ticket": ticket})

        type = request.POST.get("type")

        success, result = Ticket.update(self=ticket, buy_date=timezone.now(), quantity=quantity, type=type, event=ticket.event, user=ticket.user)

        if success:
            messages.success(request, "¡Ticket modificado!")
            return redirect("tickets")
        else:
            messages.error(request, "Error al modificar el ticket")
            return render(
                request,
                "app/buy_ticket.html",
                {
                    "ticket": ticket,
                    "errors": result,
                    "data": request.POST,
                }
            )
    else:
        print ("NO entraste al POST")

    return render(request, "app/ticket_edit.html", {"ticket": ticket})



@login_required
def create_rating(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    # Verificar que el usuario no sea el organizador
    if request.user == event.organizer:
        messages.error(request, "Los organizadores no pueden calificar sus propios eventos.")
        return redirect("event_detail", event_id=event.id)
    
    # Verificar si el usuario ya ha calificado este evento
    if Rating.objects.filter(event=event, user=request.user).exists():
        messages.error(request, "Ya has calificado este evento.")
        return redirect("event_detail", event_id=event.id)
    
    
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text", "")  # Texto es opcional
        rating = int(request.POST.get("rating"))
        
        if rating < 1 or rating > 5:
            messages.error(request, "La calificación debe estar entre 1 y 5 estrellas.")
            return render(request, "app/rating_form.html", {
                "event": event,
                "title": title,
                "text": text,
                "rating_value": rating
            })
        
        Rating.objects.create(
            title=title,
            text=text,
            rating=rating,
            event=event,
            user=request.user
        )
        messages.success(request, "Tu reseña ha sido publicada.")
        return redirect("event_detail", event_id=event.id)
            
    return render(request, "app/rating_form.html", {
        "event": event
    })


@login_required
def edit_rating(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)
    
    # Verificar que el usuario es el dueño de la calificación
    if rating.user != request.user:
        messages.error(request, "No tienes permiso para editar esta reseña.")
        return redirect("event_detail", event_id=rating.event.id)
    
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text", "")  # Texto es opcional
        rating_value = int(request.POST.get("rating"))
        
        if rating_value < 1 or rating_value > 5:
            messages.error(request, "La calificación debe estar entre 1 y 5 estrellas.")
            return render(request, "app/rating_form.html", {
                "event": rating.event,
                "rating": rating,
                "title": title,
                "text": text,
                "rating_value": rating_value
            })
        
        rating.title = title
        rating.text = text
        rating.rating = rating_value
        rating.save()
        
        messages.success(request, "Tu reseña ha sido actualizada.")
        return redirect("event_detail", event_id=rating.event.id)
            
    return render(request, "app/rating_form.html", {
        "event": rating.event,
        "rating": rating,
        "title": rating.title,
        "text": rating.text,
        "rating_value": rating.rating
    })


@login_required
def delete_rating(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)
    event_id = rating.event.id
    
    # Verificar que el usuario es el dueño de la calificación o es el organizador del evento
    if rating.user != request.user and rating.event.organizer != request.user:
        return redirect("event_detail", event_id=event_id)
    
    rating.delete()
    return redirect("event_detail", event_id=event_id)


@login_required
def add_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    # Verificar si el usuario ya ha comentado en este evento
    if Comment.objects.filter(event=event, user=request.user).exists():
        messages.error(request, "Ya has comentado en este evento. Puedes editar tu comentario existente.")
        return redirect("event_detail", event_id=event_id)
    
    if request.method == "POST":
        user = request.user
        title = request.POST.get("title")
        text = request.POST.get("text")

        if not title or not text:
            messages.error(request, "El título y el comentario son obligatorios.")
            return redirect("event_detail", event_id=event_id)
        
        Comment.objects.create(
            title=title,
            text=text,
            event=event,
            user=user
        )
        messages.success(request, "Tu comentario ha sido publicado.")
    return redirect("event_detail", event_id=event_id)


@login_required
def delete_comment(request, event_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, event_id=event_id)
    # Verificar que el usuario es el dueño del comentario o es el organizador del evento
    if comment.user != request.user and not request.user.is_organizer:
        messages.error(request, "No tienes permiso para eliminar este comentario.")
        return redirect("event_detail", event_id=event_id)
    
    if request.method == "POST":
        comment.delete()
        messages.success(request, "El comentario ha sido eliminado.")
        
    return redirect("event_detail", event_id=event_id)


@login_required
def update_comment(request, event_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, event_id=event_id)
    # Verificar que el usuario es el dueño del comentario
    if comment.user != request.user:
        messages.error(request, "No tienes permiso para editar este comentario.")
        return redirect("event_detail", event_id=event_id)
    
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        
        if not title or not text:
            messages.error(request, "El título y el comentario son obligatorios.")
            return redirect("event_detail", event_id=event_id)
        
        comment.title = title
        comment.text = text
        comment.save()
        messages.success(request, "Tu comentario ha sido actualizado.")
        
    return redirect("event_detail", event_id=event_id)


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
            'is_active': True
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


@login_required
def notification_list(request):
    if request.user.is_organizer:
        notifications = Notification.objects.all().order_by('-created_at')
        return render(request, "notifications/list.html", {"notifications": notifications, "user_is_organizer": request.user.is_organizer})
    else:
        notifications = Notification.objects.filter(users=request.user).order_by('-created_at')
        notifications_not_read = Notification.objects.filter(users=request.user, is_read=False).order_by('-created_at')
        return render(request, "notifications/list.html", {"notifications": notifications, "notifications_not_read": notifications_not_read, "user_is_organizer": request.user.is_organizer})


@login_required
def notification_create(request):
    if not request.user.is_organizer:
        return redirect("notification_list")

    if request.method == "POST":
        title = request.POST.get("title")
        message = request.POST.get("message")
        priority = request.POST.get("priority")
        destinatario = request.POST.get("destinatario")
        event_id = request.POST.get("event_id")
        usuario_id = request.POST.get("usuario_id")

        if not event_id:
            messages.error(request, "Debe seleccionar un evento.")
            return redirect("notification_create")

        event = get_object_or_404(Event, id=event_id)

        if destinatario == "usuario":
            if not usuario_id:
                messages.error(request, "Debe seleccionar un usuario.")
                return redirect("notification_create")

        notification = Notification.objects.create(
            title=title,
            message=message,
            event=event,
            priority=priority,
            created_at=timezone.now(),
        )

        if destinatario == "todos":
            asistentes = event.attendees.all()
            notification.users.set(asistentes)
        elif destinatario == "usuario" and usuario_id:
            usuario = get_object_or_404(User, pk=usuario_id)
            notification.users.set([usuario])

        notification.save()
        return redirect("notification_list")

    eventos = Event.objects.all()
    usuarios = User.objects.filter(is_organizer=False)
    return render(request, "notifications/form.html", {
        "eventos": eventos,
        "usuarios": usuarios,
    })


@login_required
def notification_edit(request, notification_id):
    if not request.user.is_organizer:
        return redirect("notification_list")

    notification = get_object_or_404(Notification, pk=notification_id)

    if request.method == "POST":
        notification.title = request.POST.get("title")
        notification.message = request.POST.get("message")
        notification.priority = request.POST.get("priority")
        recipient_ids = request.POST.getlist("recipients")
        notification.users.set(recipient_ids)
        notification.save()
        return redirect("notification_list")

    users = User.objects.filter(is_organizer=False)
    return render(request, "notifications/form.html", {"notification": notification, "users": users})


@login_required
def notification_delete(request, notification_id):
    if not request.user.is_organizer:
        return redirect("notification_list")

    notification = get_object_or_404(Notification, pk=notification_id)
    notification.delete()
    return redirect("notification_list")


@login_required
def notification_detail(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)

    if not request.user.is_organizer and request.user not in notification.users.all():
        return redirect("notification_list")

    return render(request, "notifications/detail.html", {"notification": notification})


@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, users=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification_list')


@login_required
def mark_all_notifications_read(request):
    request.user.notifications.update(is_read=True)
    return redirect('notification_list')


@login_required
def venue_form(request):
    if request.method == 'POST':
        name=request.POST.get("name")
        adress=request.POST.get("adress")
        city=request.POST.get("city")
        capacity=int(request.POST.get("capacity"))
        contact=request.POST.get("contact")


        success, venue=Venue.new(
            name=name,
            adress=adress,
            city=city,
            capacity=capacity,
            contact=contact
        )

        if success:
            return redirect('venues')

    return render(request, "app/venue_form.html")

@login_required
def venues(request):
    venues = Venue.objects.all()

    return render(
        request,
        "app/venues.html",
        {"venues": venues, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def venue_delete(request, id):
    if request.user.is_organizer:     
        venue = get_object_or_404(Venue, pk=id)

        venue.delete()

        return redirect("venues")

@login_required
def venue_edit(request, id):
    venue = get_object_or_404(Venue, pk=id)


    if request.method == "POST":
        name=request.POST.get("name")
        adress=request.POST.get("adress")
        city=request.POST.get("city")
        capacity=int(request.POST.get("capacity"))
        contact=request.POST.get("contact")


        success, updatedVenue=venue.update(
            name=name,
            adress=adress,
            city=city,
            capacity=capacity,
            contact=contact
        )

        # Validaciones básicas
        if not success:
            return render(request, "app/venue_edit_form.html", {
                "error": "Todos los campos son obligatorios.",
                "data": request.POST
            })
        else:
            return redirect('venues')

    return render(request, "app/venue_edit_form.html", {"venue": venue})