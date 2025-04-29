from django import forms
from .models import Notification

class NotificationForm(forms.ModelForm):
    class Meta:
        model  = Notification
        fields = ["user", "title", "message", "priority"]
        widgets = {"message": forms.Textarea(attrs={"rows":4})}
