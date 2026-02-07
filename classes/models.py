from django.db import models
from django.conf import settings
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

User = settings.AUTH_USER_MODEL

class PrivateClass(models.Model):
    member = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'Member'},
        related_name='member_private_classes'
    )
    trainer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'Trainer'},
        related_name='trainer_private_classes'
    )
    start_date = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.PositiveIntegerField(default=1)
    duration_months = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # total cost
    created_at = models.DateTimeField(auto_now_add=True)

    # New field
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.member} - {self.trainer} ({self.start_date} {self.start_time} for {self.duration_hours}h, {self.duration_months} months)"

    @property
    def end_time(self):
        full_datetime = datetime.combine(self.start_date, self.start_time)
        end_datetime = full_datetime + timedelta(hours=self.duration_hours)
        return end_datetime.time()

    @property
    def end_date(self):
        return self.start_date + relativedelta(months=self.duration_months)

    def calculate_price(self):
        base_rate_per_hour = 500
        experience_multiplier = 1.0

        if self.trainer and hasattr(self.trainer, 'experience_level'):
            experience_multiplier += self.trainer.experience_level / 10

        total_price = self.duration_hours * self.duration_months * base_rate_per_hour * experience_multiplier
        return total_price

    def save(self, *args, **kwargs):
        if self.price is None and self.trainer is not None:
            self.price = self.calculate_price()
        super().save(*args, **kwargs)
