from django.db import models
from django.conf import settings
from patients.models import Patient

ORDER_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
    ('refunded', 'Refunded'),
    ('failed', 'Failed'),
)

class Order(models.Model):
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    facility_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='pending')  # <- ADD DEFAULT
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order# {self.id} for {self.patient}'
    
    class Meta:
        db_table = 'orders'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=255, null=True, blank=True)
    manufacturer = models.CharField(max_length=155)
    quantity = models.PositiveIntegerField(default=0)
    mft_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.quantity} of {self.manufacturer} {self.product_name or ""}'
    
    class Meta:
        db_table = 'order items'

    
    
    
    
