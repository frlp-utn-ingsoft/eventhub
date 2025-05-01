from django.conf import settings
from django.db import models

class Comment(models.Model):
    user = models.ForeignKey(
        "app.User",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    event = models.ForeignKey(
        "app.Event",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    title = models.CharField(max_length=120)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} – {self.user}"