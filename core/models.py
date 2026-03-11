from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)
    train_id = models.CharField(max_length=20) # e.g., DART_102
    carriage_no = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(auto_now_add=True)