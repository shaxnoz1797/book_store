from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Bu yerda qo'shimcha maydonlar qo'shishimiz mumkin
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tg_id = models.BigIntegerField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.username
