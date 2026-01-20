from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
        ('CONDUCTOR', 'Conductor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class Payment(models.Model):
    TRANSACTION_TYPES = (
        ('REFILL', 'Wallet Refill'),
        ('PURCHASE', 'Pass Purchase'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"

class Pass(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='bus_pass')
    valid_until = models.DateField()
    barcode_data = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.barcode_data:
            # Generate a unique barcode data if not present
            self.barcode_data = str(uuid.uuid4())
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return self.valid_until >= timezone.now().date()

    def __str__(self):
        return f"Pass for {self.user.username} ({'Valid' if self.is_valid else 'Expired'})"
