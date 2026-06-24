from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

# Custom user model (add unique constraint for email field) use [settings.AUTH_USER_MODEL] for model relation
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
