from django.db import models
from django.conf import settings
from classes.models import PrivateClass
from django.utils import timezone
from datetime import timedelta
import uuid

User = settings.AUTH_USER_MODEL

# ---------------------------
# Membership Plans (Plan Template)
# ---------------------------
class MembershipPlan(models.Model):
    plan_name = models.CharField(max_length=50)
    duration_months = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.plan_name

# ---------------------------
# Member Subscriptions (Actual member on a plan)
# ---------------------------
class MemberSubscription(models.Model):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Automatically calculate end_date based on plan duration
        if self.plan and not self.end_date:
            start = self.start_date or timezone.now().date()
            self.end_date = start + timedelta(days=30 * self.plan.duration_months)
        super().save(*args, **kwargs)

# ---------------------------
# Payments (Can be for subscriptions or private classes)
# ---------------------------
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    )
    PAYMENT_METHOD_CHOICES = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Online', 'Online'),
    )

    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    member_subscription = models.ForeignKey(MemberSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    private_class = models.ForeignKey(PrivateClass, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.member_subscription or self.private_class
        return f"{target} - {self.payment_status} - {self.amount}"
