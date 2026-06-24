from django.db import models
from django.conf import settings

# Create your models here.

# Define house model
class House(models.Model):
    name = models.CharField(max_length=20)
    invite_code = models.CharField(max_length=6, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="houses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Only store unique HouseName per owner (composite key)
        constraints = [
            models.UniqueConstraint(
            fields=["name", "owner"], 
            name="unique_house_per_owner"
        )]

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


# Member house model
class HouseMember(models.Model):
    class Roles(models.TextChoices):
        OWNER = "owner", "Owner"
        MEMBER = "member", "Member"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=10, choices=Roles.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="house_memberships")
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="members")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "house"],
                name="unique_user_per_house"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.house.name} ({self.role})"
