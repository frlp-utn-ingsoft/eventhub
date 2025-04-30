import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import NotificationForm,TicketForm,RatingForm,CommentForm
from .models import Event, User, Notification, User_Notification,Ticket,Rating
from datetime import timedelta
from .models import Event, User, Ticket, Comment
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
    events = Event.objects.all().order_by("scheduled_at") # Los eventos
    events_with_comments = Event.objects.annotate(num_comment=Count('comment')).order_by('scheduled_at') # Los eventos pero con conteo de comentarios

    return render(
    request,
    "app/events.html",
    {
        "events": events,
        "events_with_comments": events_with_comments,
        "user_is_organizer": request.user.is_organizer,
    },
)

def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user_is_organizer = request.user == event.organizer

    comments = Comment.objects.filter(event=event)
    ratings = Rating.objects.filter(event=event)

    rating_form = RatingForm()
    comment_form = CommentForm()

    if request.method == "POST":
        if "rating" in request.POST:
            rating_form = RatingForm(request.POST)
            if rating_form.is_valid():
                rating = rating_form.save(commit=False)
                rating.event = event
                rating.user = request.user
                rating.save()
                return redirect("event_detail", event_id=event.id)
        elif "text" in request.POST:  
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.event = event
                comment.user = request.user
                comment.save()
                return redirect("event_detail", event_id=event.id)

    context = {
        "event": event,
        "user_is_organizer": user_is_organizer,
        "comments": comments,
        "ratings": ratings,
        "form": rating_form,
        "comment_form": comment_form,
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


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )

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
    notif = get_object_or_404(Notification, id = id)

    if not request.user.is_organizer:
        messages.error(request, "No tenés permiso para editar esta notificación.")
        return redirect("notifications")

    if request.method == "POST":
        form = NotificationForm(request.POST, instance=notif)

        if form.is_valid():
            notif = form.save(commit=False)
            notif.save()

            tipo_usuario = request.POST.get("tipo_usuario")
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
        initial_data = {
            "event": None,
            "user": notif.users.first() if notif.users.count() == 1 else None,
        }
        form = NotificationForm(instance=notif, initial=initial_data)

    return render(request, "app/notification_form.html", {
        "form": form,
        "notification": notif,
        "is_update": True,
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
    if not tickets:
        messages.info(request, "No tienes tickets registrados.")  
    return render(request, "app/ticket_list.html", {"tickets": tickets})


#Alta Ticket
@login_required
def ticket_create(request, event_id):
    if request.user.is_organizer:
        messages.error(request, "Los organizadores no crear tickets.")
        return redirect('home')  # Redirige 
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.event = event
            ticket.save()
            messages.success(request, "Ticket creado exitosamente.")
            return redirect("ticket_list")
    else:
        form = TicketForm()

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

    if request.method == "POST":
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket actualizado exitosamente.")
            return redirect("ticket_list")
    else:
        form = TicketForm(instance=ticket)

    return render(request, "app/ticket_form.html", {"form": form})


# Eliminar Ticket
@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    # Caso 1: Usuario regular puede eliminar su propio ticket
    if ticket.user == request.user:
        ticket.delete()
        messages.success(request, "Ticket eliminado exitosamente.")
    # Caso 2: Organizador puede eliminar tickets de sus eventos
    elif request.user.is_organizer and ticket.event.organizer == request.user:
        ticket.delete()
        messages.success(request, "Ticket eliminado exitosamente.")
    else:
        messages.error(request, "No tienes permisos para eliminar este ticket.")

    return redirect("ticket_list")

from .models import Rating
from .forms import RatingForm

@login_required
def rating_edit(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)

    # Solo el autor puede editar — organizadores no pueden editar
    if rating.user != request.user:
        messages.error(request, "No tienes permiso para editar esta reseña.")
        return redirect('event_detail', event_id=rating.event.id)


    if request.method == 'POST':
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        rating_value = request.POST.get("rating")

        # Validación del rating
        if not rating_value or not rating_value.isdigit():
            messages.error(request, "Debes seleccionar una calificación válida.")
            return redirect("rating_edit", rating_id=rating.id)

        rating_int = int(rating_value)
        if rating_int < 1 or rating_int > 5:
            messages.error(request, "La calificación debe estar entre 1 y 5.")
            return redirect("rating_edit", rating_id=rating.id)

        # Guardar cambios
        rating.title = title
        rating.text = text
        rating.rating = rating_int
        rating.save()

        messages.success(request, "Reseña actualizada exitosamente.")
        return redirect('event_detail', event_id=rating.event.id)


    return render(request, "app/rating_form.html", {"rating": rating})


@login_required
def rating_delete(request, rating_id):
    rating = get_object_or_404(Rating, id=rating_id)
    user = request.user

    # Permitir eliminación si:
    # 1) El usuario es el autor de la reseña
    # 2) El usuario es organizador del evento al que pertenece la reseña
    if rating.user == user:
        # autor elimina su propia reseña
        pass
    elif user.is_organizer:
        pass
    else:
        messages.error(request, "No tienes permiso para eliminar esta reseña.")
        return redirect('event_detail', event_id=rating.event.id)


    #Permiso concedido
    event_id = rating.event.id
    rating.delete()
    messages.success(request, "Reseña eliminada correctamente.")
    return redirect("event_detail", event_id=event_id)

#Mostrar Todos los comentarios de los eventos de un organizador
@login_required
def comentarios_organizador(request):
    if not request.user.is_authenticated or not request.user.is_organizer:
        return render(request, '403.html')  # O redirigir

    # Filtrar los comentarios de eventos cuyo organizador es el usuario logueado
    comentarios = Comment.objects.filter(event__organizer=request.user)

    return render(request, 'app/organizator_comment.html', {'comentarios': comentarios})
#Eliminar Comentarios

def delete_comment(request, comment_id):
    comentario = get_object_or_404(Comment, id=comment_id)

    # Verificar que el usuario que intenta eliminar el comentario es el mismo que lo creó
    if comentario.user == request.user:
        comentario.delete()

    return redirect('organizator_comment')  # Redirige a la vista de los comentarios o al listado de eventos
