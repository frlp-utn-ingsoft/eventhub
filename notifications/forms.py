# notifications/forms.py
from django import forms
from .models import Notification, UserNotificationStatus
from app.models import User

class NotificationForm(forms.ModelForm):

    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Destinatarios",
        help_text="Selecciona uno o más usuarios a los que enviar la notificación."
    )

    class Meta:
        model = Notification
        fields = ['title', 'message', 'priority', 'recipients']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Título de la notificación',
            'message': 'Mensaje',
            'priority': 'Prioridad',
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.request_user:
            recipient_queryset = User.objects.filter(
                is_active=True
            ).exclude(pk=self.request_user.pk)
            self.fields['recipients'].queryset = recipient_queryset
        else:
             self.fields['recipients'].queryset = User.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            current_recipient_pks = UserNotificationStatus.objects.filter(
                notification=self.instance
            ).values_list('user__pk', flat=True)
            self.fields['recipients'].initial = User.objects.filter(pk__in=current_recipient_pks)

        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                 if isinstance(field.widget, forms.CheckboxSelectMultiple):
                     pass
                 elif isinstance(field.widget, forms.Select):
                     field.widget.attrs.update({'class': 'form-select'})
                 elif not isinstance(field.widget, forms.HiddenInput):
                     field.widget.attrs.update({'class': 'form-control'})