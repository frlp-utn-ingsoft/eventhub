from django import forms
from .models import Notification

class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["title", "message", "priority", "users"]
    
    def validate(self):
        title = self.cleaned_data.get("title")
        message = self.cleaned_data.get("message")
        priority = self.cleaned_data.get("priority")

        if not title:
            self.add_error("title","El titulo no puede estar vacio.")
        elif len(title) < 10:
            self.add_error("title", "El titulo debe tener al menos 10 caracteres.")
        elif Notification.objects.filter(title = title).exists():
            self.add_error("title", "Ese titulo ya existe")
        if not message:
            self.add_error("message","El mensaje no puede estar vacio.")
        elif len(message) < 10:
            self.add_error("title", "El mensaje debe tener al menos 10 caracteres.")    
        if not priority in ["High","Medium","Low"]:
            self.add_error("priority","Prioridad invalida")
