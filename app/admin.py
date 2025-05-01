from django.contrib import admin
from .models import RefundRequest, Ticket

admin.site.register(RefundRequest)
admin.site.register(Ticket)
