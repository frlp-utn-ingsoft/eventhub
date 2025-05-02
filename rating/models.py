from django.db import models

class Rating(models.Model):
    # FKs
    user = models.ForeignKey(
        "app.User",
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    event = models.ForeignKey(
        "app.Event",
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    
    # Propiedades
    title = models.CharField(max_length=120)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Metodos
    def __str__(self):
        return f"{self.user} – {self.rating}"
