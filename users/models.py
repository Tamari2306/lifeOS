# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    age = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    daily_water_goal = models.IntegerField(default=2000)