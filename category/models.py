from django.conf import settings
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name        = models.CharField(max_length=60, unique=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name