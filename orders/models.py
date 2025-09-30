from django.db import models
from django.conf import settings
from patients.models import Patient
from product.models import Product, ProductVariant
from decimal import Decimal
# 1. IMPORT UUID
import uuid

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
    id = models.BigAutoField(primary_key=True)
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='orders')
    facility_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='pending')
    delivery_date = models.DateField(null=True, blank=True)
    order_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # 3. The __str__ representation now uses the UUID
        # Example output: 'Order# 1a2b3c4d-5e6f-7000-8888-9999aabbccdd for Patient Name'
        return f'Order# {self.id} for {self.patient}'

    class Meta:
        db_table = 'orders'

# 4. OrderItem remains largely unchanged, as Django automatically handles
# the foreign key change from an integer to a UUID.
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='ordered_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, related_name='order_items')
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.quantity} of {self.product.name if self.product else "Deleted Product"}'
    class Meta:
        db_table = 'order_items'