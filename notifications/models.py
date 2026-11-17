
from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ('Booking', 'Booking'),
        ('Cancellation', 'Cancellation'),
        ('Reminder', 'Reminder'),
        ('Flight Update', 'Flight Update'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='Booking'
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']


# Create your models here.
