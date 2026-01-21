from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class CustomUser(AbstractUser):
    """
    Custom User model supporting different roles: Admin, User, Conductor.
    Extends Django's AbstractUser.
    """
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
        ('CONDUCTOR', 'Conductor'),
    )
    # Role determines access level
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    # User's wallet balance for buying passes
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Cities"

class Route(models.Model):
    source = models.ForeignKey(City, on_delete=models.CASCADE, related_name='routes_from')
    destination = models.ForeignKey(City, on_delete=models.CASCADE, related_name='routes_to')
    cost = models.DecimalField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return f"{self.source} -> {self.destination} (₹{self.cost})"


class Payment(models.Model):
    """
    Records financial transactions (Refills and Purchases).
    """
    TRANSACTION_TYPES = (
        ('REFILL', 'Wallet Refill'),
        ('PURCHASE', 'Pass Purchase'),
        ('TICKET', 'Bus Ticket'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount}"

class Pass(models.Model):
    """
    Represents a User's Bus Pass.
    Links to a User and stores validity and barcode data.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='bus_pass')
    # Valid until removed for Pay-As-You-Go. Pass is now just an ID.
    is_active = models.BooleanField(default=True)
    # Unique identifier for the barcode
    barcode_data = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Auto-generate a unique UUID for barcode_data if not present.
        """
        if not self.barcode_data:
            self.barcode_data = str(uuid.uuid4())
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        """
        Check if the pass is currently valid. 
        For Pay-As-You-Go, it's valid if active.
        """
        return self.is_active

    def __str__(self):
        return f"Pass for {self.user.username} ({'Active' if self.is_active else 'Inactive'})"
