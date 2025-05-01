from django.db import models

class Refund(models.Model):
    user = models.ForeignKey("app.User",on_delete=models.CASCADE, related_name='refunds')
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True)
    ticket_code = models.TextField()  
    reason = models.TextField()
    detail = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} – {self.ticket_code}"
    