from django.db import models
from django.conf import settings
from inventory.models import Item


# Create your models here.

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    item_name = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    type = models.CharField(max_length=30, default="general")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        