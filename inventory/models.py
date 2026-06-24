from django.db import models
from house.models import House
from django.conf import settings

# Create your models here.

# Category model
class Category(models.Model):
    name = models.CharField(max_length=50)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints=[models.UniqueConstraint(
            fields=["name", "house"],
            name="unique_category_per_house",
            violation_error_message="Category already exists in this house"
        )]

    def __str__(self):
        return f"{self.name} ({self.house.name})"
    

# Item model
class Item(models.Model):
    name = models.CharField(max_length=25)
    barcode = models.CharField(max_length=20, unique=True, null=True)
    description = models.CharField(max_length=25)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    min_limit = models.PositiveIntegerField(default=0)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="items")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ["house", "barcode"],
                name   =  "unique_item_per_house"
        )]

    def __str__(self):
        return f"{self.name} - {self.house.name}"


#
class HistoryLog(models.Model):
    action = models.CharField(max_length=50) # created, restoked, reduced, upadated
    old_quantity = models.PositiveIntegerField(null=True, blank=True)
    new_quantity = models.PositiveIntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="history_logs")
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="history_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="history_logs")
    created_at = models.DateTimeField(auto_now_add=True)
