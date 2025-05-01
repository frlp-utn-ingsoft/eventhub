import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Event, User, RefundRequest, Ticket
from .forms import RefundRequestForm, RefundApprovalForm
from django.http import Http404


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
def my_refunds(request):
    refunds = RefundRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'app/my_refunds.html', {'reembolsos': refunds})

def refund_request(request):
    if request.method == 'POST':
        form = RefundRequestForm(request.POST)
        if form.is_valid():
            reembolso = form.save(commit=False)
            reembolso.user = request.user
            reembolso.save()
            return redirect('my_refunds') 
    else:
        form = RefundRequestForm()

    return render(request, 'app/refund_request.html', {'form': form})

@login_required
def manage_refunds(request):
    if not request.user.is_organizer:
        return redirect('my_refunds')

    if request.method == "POST":
        refund_id = request.POST.get("refund_id")
        refund = RefundRequest.objects.get(id=refund_id)
        form = RefundApprovalForm(request.POST, instance=refund)
        if form.is_valid():
            if form.cleaned_data["approve"]:
                refund.approved = True
                refund.approval_date = timezone.now()
            elif form.cleaned_data["reject"]:
                refund.approved = False
                refund.approval_date = timezone.now()
            refund.save()
        return redirect('manage_refunds')

    refunds = RefundRequest.objects.all().order_by("-created_at")
    forms_dict = {r.id: RefundApprovalForm(instance=r) for r in refunds}
    return render(request, 'app/manage_refund.html', {
        'refunds': refunds,
        'forms_dict': forms_dict
    })

def refund_detail(request, id):
    refund = get_object_or_404(RefundRequest, id=id)
    try:
        ticket = Ticket.objects.get(code=refund.ticket_code)
        event = ticket.event
    except Ticket.DoesNotExist:
        ticket = None
        event = None

    return render(request, 'app/refund_detail.html', {
        'refund': refund,
        'event': event,
        'ticket': ticket,
    })

@login_required
def edit_refund(request, id):
    refund_request = get_object_or_404(RefundRequest, id=id)
    
    if request.method == 'POST':
        form = RefundRequestForm(request.POST, instance=refund_request)
        if form.is_valid():
            form.save()
            return redirect('my_refunds') 
    else:
        form = RefundRequestForm(instance=refund_request)
    
    return render(request, 'app/refund_request.html', {'form': form})

@login_required
def delete_refund(request, id):
    refund = get_object_or_404(RefundRequest, pk=id)

    if refund.user != request.user and not request.user.is_organizer:
        return redirect("my_refunds")

    if request.method == "POST":
        refund.delete()
        return redirect("my_refunds")

    return redirect("my_refunds")