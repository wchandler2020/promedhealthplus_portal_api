from django.db import models
from django.conf import settings
# Create your models here.

NOTIFICATION_TYPE_CHOICES = [
    ('new_patient', 'New Patient'),
    ('new_order', 'New Order'),
    ('announcement', 'Announcement'),
]

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.type} for {self.recipient}'