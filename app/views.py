import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Category, Event, User, refund


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
    categories = Category.objects.all()
    return render(request, "app/event_detail.html", {"event": event, "categories": categories})


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
        category_id = request.POST.get("category")
        category = None
        if category_id is not None:
            category = get_object_or_404(Category, pk=category_id)
        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, category, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, category, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    categories = Category.objects.all()
    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categories": categories},
    )

@login_required
def category_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("name")
        description = request.POST.get("description")
        if id is None:
            Category.new(title, description, is_active=True)
        else:
            category = get_object_or_404(Category, pk=id)
            category.update(title, description, request.user, is_active=True)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) # refresh last screen


@login_required
def Refund_create(request):
    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        
        """
        DESCOMENTAR CUANDO SE IMPLEMENTE LA PARTE DE TICKETS

        if ticket.was_used or (timezone.now() - ticket.purchase_date).days > 30:
            return render(
                request,
                "app/refund_form.html",
                {"error": "El ticket ya fue usado o han pasado más de 30 días desde su compra."}
            )
            """
        refund.objects.create(ticket_code=ticket_code,
                              reason=reason,
                              user=request.user)
        


        return redirect("my_refunds")
    return render(request, "refund/refund_form.html")

@login_required
def My_refunds(request):
    refunds = refund.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "refund/my_refunds.html", {"refunds": refunds})

@login_required
def Refund_edit(request, id):
    refund_obj = get_object_or_404(refund, id=id, user=request.user)

    if refund_obj.aproved:  # Ya la vio un organizer
        return redirect("my_refunds")

    if request.method == "POST":
        refund_obj.ticket_code = request.POST.get("ticket_code")
        refund_obj.reason = request.POST.get("reason")
        refund_obj.save()
        return redirect("my_refunds")

    return render(request, "refund/refund_form.html", {"refund": refund_obj})

@login_required
def Refund_delete(request, id):
    refund_obj = get_object_or_404(refund, id=id, user=request.user)
    if not refund_obj.aproved:  # Ya la vio un organizer
        refund_obj.delete()

    return redirect("my_refunds")