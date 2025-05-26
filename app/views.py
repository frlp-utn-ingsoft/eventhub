import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import NotificationForm,TicketForm,RefundRequestForm,RatingForm,CommentForm, VenueForm, EventForm, SurveyForm
from .models import Event, User, Notification, User_Notification,Ticket, Rating, RefundRequest
from datetime import timedelta
from .models import (
    Category,
    Comment,
    Event,
    Notification,
    RefundRequest,
    Ticket,
    Rating,
    User,
    User_Notification,
    Venue,
    SurveyResponse
)
from django.db.models import Count

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
    show_past = request.GET.get("show_past") == "1"  # Checkbox marcada

    if show_past:
        events = Event.objects.all().order_by("scheduled_at")
    else:
        events = Event.objects.filter(scheduled_at__gte=timezone.now()).order_by("scheduled_at")

    events_with_comments = events.annotate(num_comment=Count('comment'))

    return render(
    request,
    "app/events.html",
    {
        "events": events,
        "events_with_comments": events_with_comments,
        "user_is_organizer": request.user.is_organizer,
    },
)

@login_required
def event_detail(request, event_id):
    #event = get_object_or_404(Event, pk=id)
    event = get_object_or_404(Event.objects.prefetch_related("categories"), id=event_id)
    user_is_organizer = request.user == event.organizer

    ratings = event.rating.all() # type: ignore 
    comments = event.comment.all()  # type: ignore # related_name='comment'

    if request.method == 'POST':
        if 'comment_submit' in request.POST:
            title = request.POST.get('title')  # corregido 'tittle' -> 'title'
            text = request.POST.get('text')
            Comment.objects.create(
                tittle=title,
                text=text,
                user=request.user,
                event=event,
                created_date=timezone.now()
            )
            return redirect('event_detail', event_id=event_id)

        elif 'rating_submit' in request.POST:
                title = request.POST.get('title')  # corregido 'tittle' -> 'title'
                text = request.POST.get('text')
                rating_value = request.POST.get('rating')
                Rating.objects.create(
                    title=title,
                    text=text,
                    rating=int(rating_value),
                    user=request.user,
                    event=event,
                    created_at=timezone.now()
                )

                return redirect('event_detail', event_id=event_id)

    comments = Comment.objects.filter(event=event).order_by("-created_date")
    ratings = Rating.objects.filter(event=event)

    context = {
        "event": event,
        "user_is_organizer": user_is_organizer,
        "comments": comments,
        "ratings": ratings,
        "num_comments": comments.count(),
        "num_ratings": ratings.count(),
    }
    return render(request, "app/event_detail.html", context)

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

#modifique event_form
@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if id:
        instance = get_object_or_404(Event, pk=id)
    else:
        instance = None

    if request.method == "POST":
        form = EventForm(request.POST, instance=instance)

        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user

            # Combinar date y time desde POST para formar scheduled_at
            date = request.POST.get("date")
            time = request.POST.get("time")
            if date and time:
                try:
                    y, m, d = map(int, date.split("-"))
                    h, mi = map(int, time.split(":"))
                    event.scheduled_at = timezone.make_aware(datetime.datetime(y, m, d, h, mi))
                except Exception:
                    form.add_error(None, "Fecha y hora inválidas.")
                    return render(request, "app/event_form.html", {
                        "form": form,
                        "user_is_organizer": request.user.is_organizer
                    })

            event.save()
            form.save_m2m()

            return redirect("events")
        else:
            messages.error(request, "Corregí los errores.")
    else:
        # Cargar el form con instancia si hay edición
        initial = {}
        if instance:
            initial['date'] = instance.scheduled_at.date()
            initial['time'] = instance.scheduled_at.time().strftime("%H:%M")

        form = EventForm(instance=instance, initial=initial)

    return render(request, "app/event_form.html", {
        "form": form,
        "user_is_organizer": request.user.is_organizer
    })

@login_required
def notifications(request):
    user = request.user 

    if user.is_organizer:
        notifications = Notification.objects.all().order_by("priority")
    else:
        notifications = Notification.objects.filter(users=user).order_by("priority")

    user_notifications = {
        un.notification.id: un.is_read
        for un in User_Notification.objects.filter(user = user)
    }
    return render(
        request,
        "app/notifications.html",
        {"notifications": notifications, "user_is_organizer": request.user.is_organizer,"user_notifications": user_notifications,},
    )

@login_required
def notification_create(request):
    if not request.user.is_organizer:
        messages.error(request, "Debes ser organizador para crear notificaciones.")
        return redirect("notification")

    if request.method == "POST":
        form = NotificationForm(request.POST)

        if form.is_valid():
            notif = form.save(commit=False)
            notif.save()

            tipo_usuario = request.POST.get("tipo_usuario")
            event = form.cleaned_data.get("event")
            specific_user = form.cleaned_data.get("user")

            if tipo_usuario == "all" and event:
                user_ids = (
                    Ticket.objects.filter(event=event)
                    .values_list("user_id", flat=True)
                    .distinct()
                )
                notif.users.set(user_ids)

            elif tipo_usuario == "specific" and specific_user:
                notif.users.set([specific_user])

            messages.success(request, "Notificación creada correctamente.")
            return redirect("notifications")
        else:
            messages.error(request, "Errores en el formulario.")
    else:
        form = NotificationForm()

    return render(request, "app/notification_form.html", {
        "form": form,
        "is_update": False,
    })

@login_required
def notification_update(request, id):
    notif = get_object_or_404(Notification, id=id)

    if not request.user.is_organizer:
        messages.error(request, "No tenés permiso para editar esta notificación.")
        return redirect("notifications")

    if request.method == "POST":
        tipo_usuario = request.POST.get("tipo_usuario", "all")
        form = NotificationForm(request.POST, instance=notif)

        if form.is_valid():
            notif = form.save(commit=False)
            notif.save()

            event = form.cleaned_data.get("event")
            specific_user = form.cleaned_data.get("user")

            notif.users.clear()

            if tipo_usuario == "all" and event:
                user_ids = (
                    Ticket.objects.filter(event=event)
                    .values_list("user_id", flat=True)
                    .distinct()
                )
                notif.users.set(user_ids)
            elif tipo_usuario == "specific" and specific_user:
                notif.users.set([specific_user])

            messages.success(request, "Notificación actualizada correctamente.")
            return redirect("notifications")
        else:
            messages.error(request, "Errores en el formulario.")
    else:
        specific_user = notif.users.first() if notif.users.count() == 1 else None
        tipo_usuario = "specific" if specific_user else "all"

        initial_data = {
            "event": notif.event,
            "user": specific_user if tipo_usuario == "specific" else None,
        }

        form = NotificationForm(instance=notif, initial=initial_data)

    return render(request, "app/notification_form.html", {
        "form": form,
        "notification": notif,
        "is_update": True,
        "tipo_usuario": tipo_usuario,
    })

@login_required
def notification_delete(request,id):
    user = request.user
    notification = get_object_or_404(Notification,id = id)
    
    if not user.is_organizer:
        return redirect("notifications")
    
    if request.method == "POST" :
        notification.delete()
        messages.success(request,"Notificacion eliminada correctamente.")
        return redirect("notifications")
    
    return render(request,"app/notification_delete.html", {"notification":notification})

@login_required
def is_read(request, notification_id):
    user = request.user

    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id)
        user_notification, _ = User_Notification.objects.get_or_create(
            user=user, notification=notification
        )
        user_notification.is_read = True
        user_notification.save()

    return redirect("notifications")

@login_required
def all_is_read(request):
    
    if request.method == "POST":
        notifications = Notification.objects.filter(users=request.user)
        for n in notifications:
            un, _ = User_Notification.objects.get_or_create(user=request.user, notification=n)
            un.is_read = True
            un.save()
    return redirect("notifications")

#Listado de todos los tickets del user
@login_required
def ticket_list(request):
    print(request.user)
    tickets = Ticket.objects.filter(user=request.user)
    print(tickets)  
    return render(request, "app/ticket_list.html", {"tickets": tickets})


#Alta Ticket
@login_required
def ticket_create(request, event_id):
    if request.user.is_organizer:
        messages.error(request, "Los organizadores no crear tickets.")
        return redirect('home')  # Redirige 
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = TicketForm(request.POST, user=request.user, event=event)
        if form.is_valid():
            ticket = form.save(commit=False)  
            ticket.user = request.user
            ticket.event = event
            ticket.save()
            messages.success(request, "Ticket creado exitosamente.", extra_tags='ticket')
            return redirect("satisfaction_survey", ticket_id=ticket.id)
    else:
        form = TicketForm(user=request.user, event=event)

    return render(request, "app/ticket_form.html", {"form": form, "event": event})


#Editar Ticket (solo si es dueño)
@login_required
def ticket_update(request, ticket_id):
    if request.user.is_organizer:
        messages.error(request, "Los organizadores no modificar tickets.")
        return redirect('home')  # Redirige
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Solo el dueño puede editar su ticket
    if ticket.user != request.user:
        messages.error(request, "No tienes permisos para editar este ticket.")
        return redirect("ticket_list")

    event = ticket.event 

    if request.method == "POST":
        form = TicketForm(request.POST, instance=ticket, user=request.user, event=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket actualizado exitosamente.", extra_tags='ticket')
            return redirect("ticket_list")
    else:
        form = TicketForm(instance=ticket, user=request.user, event=event)

    return render(request, "app/ticket_form.html", {"form": form,  'event': event})


# Eliminar Ticket
@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Caso 1: Usuario regular puede eliminar su propio ticket
    if ticket.user == request.user:
        ticket.delete()
        messages.success(request, "Ticket eliminado exitosamente.", extra_tags='ticket')
    # Caso 2: Organizador puede eliminar tickets de sus eventos
    elif request.user.is_organizer and ticket.event.organizer == request.user:
        ticket.delete()
        messages.success(request, "Ticket eliminado exitosamente.", extra_tags='ticket')
    else:
        messages.error(request, "No tienes permisos para eliminar este ticket.")

    return redirect("ticket_list")

@login_required
def rating_edit(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)

    # Solo el autor puede editar — organizadores no pueden editar
    if rating.user != request.user:
        messages.error(request, "No tienes permiso para editar esta reseña.")
        return redirect('event_detail', event_id=rating.event.id) # type: ignore


    if request.method == 'POST':
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        rating_value = request.POST.get("rating")

        # Validación del rating
        if not rating_value or not rating_value.isdigit():
            messages.error(request, "Debes seleccionar una calificación válida.")
            return redirect("rating_edit", rating_id=rating.id) # type: ignore

        rating_int = int(rating_value)
        if rating_int < 1 or rating_int > 5:
            messages.error(request, "La calificación debe estar entre 1 y 5.")
            return redirect("rating_edit", rating_id=rating.id) # type: ignore

        # Guardar cambios
        rating.title = title
        rating.text = text
        rating.rating = rating_int
        rating.save()

        messages.success(request, "Reseña actualizada exitosamente.")
        return redirect('event_detail', event_id=rating.event.id) # type: ignore


    return render(request, "app/rating_form.html", {"rating": rating})


@login_required
def rating_delete(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)
    user = request.user

    if rating.user == user or user.is_organizer:
        rating.delete()
        messages.success(request, "Reseña eliminada correctamente.")
    else:
        messages.error(request, "No tienes permiso para eliminar esta reseña.")

    return redirect('event_detail', event_id=rating.event.id) # type: ignore

#Mostrar Todos los comentarios de los eventos de un organizador
@login_required
def comentarios_organizador(request):
    if not request.user.is_authenticated or not request.user.is_organizer:
        return render(request, '403.html')  # O redirigir

    # Filtrar los comentarios de eventos cuyo organizador es el usuario logueado
    comentarios = Comment.objects.filter(event__organizer=request.user)

    return render(request, 'app/organizator_comment.html', {'comentarios': comentarios})
#Eliminar Comentarios
@login_required
def delete_comment(request, comment_id):
    comentario = get_object_or_404(Comment, id=comment_id)

    # Obtener el evento asociado al comentario
    evento = comentario.event  # Suponiendo que el comentario tiene un campo 'evento' como clave foránea.

    # Comprobar si el usuario actual es el organizador del evento o es el usuario que lo creó
    if evento.organizer == request.user: # type: ignore
        comentario.delete()
        messages.success(request, "Comentario eliminado con éxito.")
        return redirect('organizator_comment')
    elif comentario.user == request.user:
        comentario.delete()
        messages.success(request, "Comentario eliminado con éxito.")
        return redirect('event_detail',event_id=comentario.event.id) # type: ignore
    else:
        messages.error(request, "No tienes permiso para eliminar este comentario, solo el organizador del evento puede hacerlo.")
        return redirect('event_detail',event_id=comentario.event.id) # type: ignore

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        messages.error(request, "No tienes permiso para editar este comentario.")
        return redirect('event_detail', event_id=comment.event.id) # type: ignore

    if request.method == 'POST':
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()

        errors = {}
        if not title:
            errors["title"] = "El título no puede estar vacío."
        if not text:
            errors["text"] = "El comentario no puede estar vacío."

        if errors:
            for error in errors.values():
                messages.error(request, error)
            return render(request, "app/comment_edit.html", {"comment": comment})

        comment.tittle = title
        comment.text = text
        comment.save()

        messages.success(request, "Comentario actualizado exitosamente.")
        return redirect('event_detail', event_id=comment.event.id) # type: ignore

    return render(request, "app/comment_edit.html", {"comment": comment})


    
    return redirect('organizator_comment')
#////////////////////////////////////////////////////////REEMBOLSOS//////////////////////////////////////////////////////////////
@login_required #Solicitud de reembolso
def refund_request(request, ticket_code):
    ticket = get_object_or_404(Ticket, ticket_code=ticket_code)

    if request.method == "POST":
        reason = request.POST.get("reason")
        if not reason:
            return redirect("ticket_detail", ticket_code=ticket_code)

        # Crear solicitud de reembolso
        refund = RefundRequest.new(
            ticket_code=ticket.ticket_code,
            reason=reason,
            user=request.user
        )

        if refund[0]:
            return redirect("events")
        else:
            return render(request, "app/refund_request.html", {"errors": refund[1]})

    return render(request, "app/refund_request.html", {"ticket": ticket})

@login_required
def handle_refund_request(request, refund_id):
    # Verifica si el usuario es organizador
    if not request.user.is_organizer:
        return redirect("events")

    # Obtén la solicitud de reembolso
    refund_request = get_object_or_404(RefundRequest, pk=refund_id)

    if request.method == "POST":
        action = request.POST.get("action")

        # Si se acepta la solicitud de reembolso
        if action == "accept":
            refund_request.approved = True
            refund_request.approval_date = timezone.now().date()  # Marca la fecha de aprobación
            refund_request.save()


        # Si se rechaza la solicitud de reembolso
        elif action == "reject":
            refund_request.approved = False
            refund_request.approval_date = None  # Borra la fecha de aprobación
            refund_request.save()

        return redirect("refund_requests")  # Redirige a la vista que lista las solicitudes de reembolso

    return render(
        request,
        "app/handle_refund_request.html",  # Plantilla para confirmar la acción
        {"refund_request": refund_request}
    )



@login_required
def refund_list(request):
    if not request.user.is_organizer:
        return redirect("events")
    refunds = RefundRequest.objects.all()
    return render(request, 'app/refund_list.html', {'refunds': refunds})

@login_required
def approve_refund(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    refund.approved = True
    refund.approval_date = timezone.now()
    refund.save()
    return redirect('refund_list')

@login_required
def reject_refund(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    refund.approved = False
    refund.approval_date = timezone.now()
    refund.save()
    return redirect('refund_list')

@login_required
def delete_refund(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    refund.delete()
    return redirect('refund_list')

# --- VISTA DEL USUARIO ---

@login_required
def create_refund(request):
    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.user = request.user
            refund.created_at = timezone.now()
            refund.save()
            return redirect('refund_list')  # Redirige a la lista de solicitudes de reembolso
    else:
        form = RefundRequestForm()
    return render(request, 'app/create_refund.html', {'form': form})

@login_required
def refund_update(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    approved_value = request.POST.get("approved")

    if approved_value is not None:
        refund.approved = approved_value.lower() == "true"
        refund.approval_date = timezone.now()
        refund.save()

    return redirect("refund_list")

@login_required
def user_refund_list(request):
    refunds = RefundRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'app/user_refund_list.html', {'refunds': refunds})

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

def list_categories(request):
    categories = Category.objects.annotate(event_count=Count('event')).all()
    return render(request, 'app/category_list.html', {'categories': categories})


def category_form(request):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
        
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        active = request.POST.get("active") == "on"  # Checkbox para permitir el activo o no
        Category.objects.create(name=name, description=description, active=active)
        
        
        

        return redirect("list_categories")  # Retorno devuelta al listado de categorias

    category = {}

    return render(request, "app/category_form.html", {"category": category})




def update_category(request,id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
            name=request.POST.get("name")
            description=request.POST.get("description")
            active=request.POST.get("active") == "on"
            category.name=name
            category.description=description
            category.active=active
            category.save()
            return redirect("list_categories") 
    return render(request, "app/category_form.html", {"category": category, "update":True})


def delete_category(request, id):
    category = get_object_or_404(Category, pk=id)
    if request.method == 'POST':
        category.delete()
        return redirect('/categories/')
    return redirect('/categories/')

#Listado de todos los Venue (solo para organizadores)
@login_required
def venue_list(request):
    print(request.user)
    if not request.user.is_organizer:
        messages.error(request, "Los usuarios no pueden visualizar ubicaciones.")
        return redirect("events")  # Redirige a la lista de eventos si no es organizador
    venues = Venue.objects.all()
    print(venues)   
    return render(request, "app/venue_list.html", {"venues": venues})


#Alta Venue (solo para organizadores)
@login_required
def venue_create(request):
    if not request.user.is_organizer:
        messages.error(request, "Los usuarios no pueden crear ubicaciones.")
        return redirect("events")

    if request.method == "POST":
        form = VenueForm(request.POST)
        if form.is_valid():
            messages.success(request, "Ubicación creada exitosamente.", extra_tags='ubicacion')
            form.save()
            return redirect("venue_list")
    else:
        form = VenueForm()
    return render(request, "app/venue_form.html", {"form": form, "action": "Crear"})


#Editar Venue (solo para organizadores)
@login_required
def venue_update(request, venue_id):
    if not request.user.is_organizer:
        messages.error(request, "Los usuarios no pueden modificar ubicaciones.")
        return redirect("events")
    venue = get_object_or_404(Venue, id=venue_id)

    if request.method == "POST":
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, "Ubicación actualizada exitosamente.", extra_tags='ubicacion')
            return redirect("venue_list")
    else:
        form = VenueForm(instance=venue)

    return render(request, "app/venue_form.html", {"form": form, "action": "Editar"})


@login_required
def venue_delete(request, venue_id):
    """Elimina un venue existente."""
    if not request.user.is_organizer:
        messages.error(request, "Los usuarios no pueden eliminar ubicaciones.")
        return redirect("events")
    venue = get_object_or_404(Venue, pk=venue_id)
    if request.method == "POST":
        venue.delete()
        messages.success(request, "Ubicación eliminada exitosamente.", extra_tags='ubicacion')
    return redirect("venue_list") # Siempre redirige a la lista de venues

   

    return redirect('organizator_comment')  # Redirige a la vista de los comentarios o al listado de eventos


@login_required
def satisfaction_survey(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)

    if hasattr(ticket, 'surveyresponse'):
        messages.info(request, "Ya completaste la encuesta.")
        return redirect("ticket_list")

    if request.method == 'POST':
        form = SurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.ticket = ticket
            survey.save()
            messages.success(request, "Gracias por responder la encuesta.")
            return redirect("ticket_list")
    else:
        form = SurveyForm(initial={'satisfaction': 0})

    return render(request, "app/survey_form.html", {"form": form, "ticket": ticket})

@login_required
def survey_list(request):
    if not request.user.is_organizer:
        messages.error(request, "Solo los organizadores pueden ver las encuestas.")
        return redirect("home")

    surveys = SurveyResponse.objects.select_related("ticket", "ticket__event", "ticket__user")
    return render(request, "app/survey_list.html", {"surveys": surveys})