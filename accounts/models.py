from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
# Create your models here.
from .manager import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    """
    User
    """
    name = models.CharField(max_length=500)
    phone = models.CharField(max_length=20, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    def __str__(self):
        return f"{self.phone} "


