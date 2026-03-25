from django.db import models
import uuid

# Create your models here.

class EmailVerification(models.Model):
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email
