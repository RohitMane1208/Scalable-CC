from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    passenger = models.ForeignKey(User, on_delete=models.CASCADE)
    train_id = models.CharField(max_length=20) # e.g., DART_102
    carriage_no = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)
    verified_at = models.DateTimeField(auto_now_add=True)

class EmergencyRequest(models.Model):
    """
    Tracks security/emergency requests raised by users for their history dashboard
    and for administrative audit trails.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=255)  # Name of the Hospital/Police Station
    service_type = models.CharField(max_length=100)  # Category (e.g., Medical, Police)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        ordering = ['-timestamp']  # Shows the most recent requests first

    def __str__(self):
        return f"{self.user.email} - {self.service_name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"