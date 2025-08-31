from django.db import models
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    manufacturer = models.CharField(max_length=155)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True, default='images/default_item.png')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} by {self.manufacturer}"

    class Meta:
        db_table = 'products'
        ordering = ['name']
