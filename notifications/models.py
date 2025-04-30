from django.db import models


class Notification(models.Model):
    PRIORITY_CHOICES = [
        ('HIGH', 'Alta'),
        ('MEDIUM', 'Media'),
        ('LOW', 'Baja'),
    ]
    
    user = models.ForeignKey("app.User", on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='LOW')
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']