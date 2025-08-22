from django.db import models

# Create your models here.
class SalesRep(models.Model):
    name = models.CharField(max_length=150, verbose_name='Representative Name', null=True, blank=True)
    email = models.EmailField(verbose_name='Representative Email Address', null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name='Representative Phone Number', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
