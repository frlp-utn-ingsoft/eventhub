import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from .models import Event, User, Location, Category, Notification, NotificationXUser, Comments, Ticket


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_superuser = request.POST.get("is-superuser") is not None
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
                email=email, username=username, password=password, is_superuser=is_superuser
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
        {"events": events, "user_is_is_superuser": request.user.is_superuser},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    comments = Comments.objects.filter(event=event).order_by('-created_at')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        errors = {}

        if not title:
            errors['title'] = "El título no puede estar vacío."
        if not description:
            errors['description'] = "La descripción no puede estar vacía."

        if not errors:
            Comments.objects.create(
                title=title,
                description=description,
                user=request.user,
                event=event
            )
            return redirect('event_detail', id=event.id)

        # Si hay errores, los devolvemos al template
        return render(request, 'app/event_detail.html', {
            'event': event,
            'comments': comments,
            'errors': errors,
            'title': title,
            'description': description,
            'user_is_organizer': event.organizer == request.user
        })

    # GET request normal
    return render(request, 'app/event_detail.html', {
        'event': event,
        'comments': comments,
        'user_is_organizer': event.organizer == request.user
    })


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_superuser:
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
        location_id = request.POST.get("location")
        location = Location.objects.filter(id=location_id).first() if location_id else None
        category_ids = request.POST.getlist("categories")
        categories = Category.objects.filter(id__in=category_ids)


        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            event, errors = Event.new(title, description, scheduled_at, request.user, location)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, location)

        if event:
            event.categories.set(categories)
        return redirect("events")

    
    
    event = {}
    locations = Location.objects.all()
    categories = Category.objects.all()

    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user.is_organizer": request.user.is_organizer, "locations": locations, "categories": categories},
    )



@login_required
def list_locations(request):
    locations = Location.objects.all() # Las más nuevas primero
    return render(request, 'locations/list_locations.html', {'locations': locations})

@login_required
def create_location(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        # Validar datos
        errors = Location.validate(name, address, city, int(capacity) if capacity else None, contact)

        if errors:
            # Si hay errores, renderizamos el formulario otra vez, mostrando errores
            return render(request, 'locations/create_location.html', {
                'errors': errors,
                'form_data': request.POST,
            })

        # Si no hay errores, creamos la Location
        Location.new(name, address, city, int(capacity), contact)
        return redirect('locations_list')  # Redirigimos a una lista o donde quieras

    return render(request, 'locations/create_location.html')

def update_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        capacity = request.POST.get('capacity')
        contact = request.POST.get('contact')

        errors = Location.validate(name, address, city, int(capacity) if capacity else None, contact)

        if errors:
            return render(request, 'locations/update_location.html', {
                'location': location,
                'errors': errors,
                'form_data': request.POST,
            })

        location.update(name=name, address=address, city=city, capacity=int(capacity), contact=contact)
        return redirect('locations_list')

    return render(request, 'locations/update_location.html', {'location': location})

def delete_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    location.delete()
    return redirect('locations_list')

@login_required
def list_categories(request):
    categories = Category.objects.annotate(event_qty=Count('eventcategory'))
    return render(request, 'categories/list_categories.html', {'categories': categories})

@login_required
def manage_category(request, category_id=None):
    category = None
    if category_id:
        category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on' if category else True

        errors = Category.validate(name, description)

        if errors:
            return render(request, 'categories/create_category.html', {
                'category': category,
                'errors': errors,
                'form_data': request.POST,
            })

        if category:
            category.update(name=name, description=description, is_active=is_active)
        else:
            Category.new(name, description)

        return redirect('categories_list')

    return render(request, 'categories/create_category.html', {
        'category': category
    })
    
@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect('categories_list')

@login_required
def create_notification(request, notification_id=None):
    user = request.user
    if not user.is_superuser:
        return redirect("list_notifications")
    
    events = Event.objects.all()
    users = User.objects.all()

    notification = None
    if notification_id:
        notification = get_object_or_404(Notification, id=notification_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        event_id = request.POST.get('event')
        priority = request.POST.get('priority')
        recipient_type = request.POST.get('recipients')
        specific_user_id = request.POST.get('userSelect') if recipient_type == 'specific' else None

        errors = Notification.validate(title, message, event_id, recipient_type, specific_user_id)
        if errors:
            return render(request, 'notifications/create_notification.html', {
                'events': events,
                'users': users,
                'errors': errors,
                'form_data': request.POST,
                'notification': notification,
            })

        event_selected = Event.objects.get(id=event_id)
        if notification:

            notification.title = title
            notification.message = message
            notification.event = event_selected
            notification.priority = priority
            notification.save()


            NotificationXUser.objects.filter(notification=notification).delete()
        else:

            notification = Notification.new(title, message, event_selected, priority)


        if recipient_type == 'all':
            for user in users:
                NotificationXUser.objects.create(notification=notification, user=user)
        elif recipient_type == 'specific' and specific_user_id:
            specific_user = User.objects.get(id=specific_user_id)
            NotificationXUser.objects.create(notification=notification, user=specific_user)


        return redirect('list_notifications')


    return render(request, 'notifications/create_notification.html', {
        'events': events,
        'users': users,
        'notification': notification,
    })

@login_required
def list_notifications(request):
    search = request.GET.get('search', '')
    event_filter = request.GET.get('event_filter', '')
    priority_filter = request.GET.get('priority_filter', '')

    if request.user.is_staff:  # user admin
        notifications = Notification.objects.all()
        if search:
            notifications = notifications.filter(title__icontains=search)
        if event_filter:
            notifications = notifications.filter(event_id=event_filter)
        if priority_filter:
            notifications = notifications.filter(priority=priority_filter)

        events = Event.objects.all()
        users = User.objects.all()

        return render(request, 'notifications/notifications_admin.html', {
            'notifications': notifications,
            'events': events,
            'users': users,
        })
    else:  # user normal
        notifications = NotificationXUser.objects.filter(user=request.user).select_related('notification')
        unread_count = notifications.filter(is_read=False).count()
        return render(request, 'notifications/notifications_user.html', {
            'notifications': notifications,
            'unread_count': unread_count,
        })

@login_required
def delete_notification(request, notification_id):
    user = request.user
    if not user.is_superuser:
        return redirect("list_notifications")
    
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    return redirect('list_notifications')

@login_required
def read_notification(request, notification_user_id):
    notification_user = get_object_or_404(NotificationXUser, id=notification_user_id, user=request.user)
    notification_user.is_read = True
    notification_user.save()
    return redirect('list_notifications')

@login_required
def read_all_notifications(request):
    NotificationXUser.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('list_notifications')
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comments, pk=comment_id, user=request.user)

    if request.method == "POST":
        comment.title = request.POST.get('title', '')
        comment.description = request.POST.get('description', '')
        comment.save()
        return redirect('event_detail', id=comment.event.id)

    return render(request, 'comments/edit_comment.html', {'comment': comment})

def delete_comment(request, comment_id):
    try:
        comment = Comments.objects.get(id=comment_id)
    except Comments.DoesNotExist:
        messages.error(request, "Comentario no encontrado.")
        return redirect('event_list')
    
    if request.user != comment.user and not request.user.is_staff:
        messages.error(request, "No tienes permiso para eliminar este comentario.")
        return redirect('event_detail', id=comment.event.id)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, "Comentario eliminado exitosamente.")
        return redirect('event_detail', id=comment.event.id)

    return render(request, 'comments/delete_comment.html', {'comment': comment})


def detail_comment(request, comment_id):
    comment = get_object_or_404(Comments, pk=comment_id)
    return render(request, 'comments/detail_comment.html', {'comment': comment})


@login_required
def buy_ticket(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user = request.user
    context = {'event': event}

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            ticket_type = request.POST.get("ticket_type")
            quantity = int(request.POST.get("quantity", 1))
            
            # Validaciones básicas
            if quantity < 1 or quantity > 10:
                raise ValueError("La cantidad debe estar entre 1 y 10")
            
            if ticket_type not in [choice[0] for choice in Ticket.TICKET_TYPES]:
                raise ValueError("Tipo de entrada inválido")

            # Crear tickets
            for _ in range(quantity):
                Ticket.objects.create(
                    user=user,
                    event=event,
                    type=ticket_type,
                    # El ticket_code se genera automáticamente en el save()
                )

            return redirect('tickets_list')  # Redirigir a lista de tickets

        except Exception as e:
            context['error'] = str(e)
            return render(request, 'tickets/buy_ticket.html', context)

    # GET: Mostrar formulario de compra
    return render(request, 'tickets/buy_ticket.html', context)


@login_required
def tickets_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, "tickets/tickets_list.html", {"tickets": tickets})