import datetime
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Trainer', 'Trainer'),
        ('Member', 'Member'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Member')
    phone = models.CharField(max_length=15, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    
    # Trainer-specific fields
    specialization = models.CharField(max_length=100, null=True, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)
    
    # Member-specific / general fields
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fitness_goal = models.CharField(max_length=100, null=True, blank=True)
    membership_start_date = models.DateField(null=True, blank=True)

    # Admin-created accounts must set password on first login
    must_set_password = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        # Force role='Admin' if creating superuser
        if self.is_superuser:
            self.role = 'Admin'
        super().save(*args, **kwargs)


class WeightLog(models.Model):
    """
    Track user weight over time for progress monitoring
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this entry")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']  # One entry per user per day
    
    def __str__(self):
        return f"{self.user.username} - {self.weight}kg on {self.date}"
    
    @property
    def bmi(self):
        """Calculate BMI if height is available"""
        if self.user.height and self.user.height > 0:
            height_m = float(self.user.height) / 100  # Convert cm to meters
            return round(float(self.weight) / (height_m ** 2), 1)
        return None
