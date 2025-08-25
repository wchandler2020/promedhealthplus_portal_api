from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.conf import settings
from django.utils import timezone
from sales_rep.models import SalesRep
from phonenumber_field.modelfields import PhoneNumberField
import random

# For reference/display purposes only — NOT used to prefix phone numbers
COUNTRY_CODE_CHOICES = (
    ('+1', 'United States'),
    ('+1', 'Canada'),
    ('+44', 'United Kingdom'),
    ('+33', 'France'),
    ('+39', 'Italy'),
    ('+49', 'Germany'),
    ('+34', 'Spain'),
)

verification_methods = (
    ('email', 'Email'),
    ('sms', 'SMS'),
)

ROLES = (
    ('Primary Care Provider', 'Primary Care Provider'),
    ('Nurse', 'Nurse'),
    ('Administrator', 'Administrator'),
    ('Medical Supply Technician', 'Medical Supply Technician'),
)

def generate_code():
    return str(random.randint(100000, 999999))


class User(AbstractUser):
    username = models.CharField(unique=True, max_length=255)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)

    # ✅ Ensure this stores a full E.164 number (e.g., +15551234567)
    phone_number = PhoneNumberField(null=True, blank=True)

    # ✅ Just for reference/display – not used for combining with phone_number
    country_code = models.CharField(
        max_length=5, 
        choices=COUNTRY_CODE_CHOICES, 
        default='+1',
        help_text="Country dial code for reference (e.g. +1 for US)."
    )

    otp = models.CharField(max_length=100, null=True, blank=True)
    refresh_token = models.CharField(max_length=1000, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self) -> str:
        return f'{self.email} | {self.date_joined}'

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0] if '@' in self.email else self.email
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip() or self.username
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(SalesRep, on_delete=models.SET_NULL, null=True, blank=True, related_name="providers")
    image = models.FileField(upload_to='images', default=f'{settings.MEDIA_URL}images/default_user.jpg', null=True, blank=True)
    role = models.CharField(max_length=200, choices=ROLES, null=True, blank=True)
    facility = models.CharField(max_length=200, null=True, blank=True)
    facility_phone_number = models.CharField(max_length=20, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.full_name or self.user.username)

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.user.username
        super().save(*args, **kwargs)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def post_save_profile(sender, instance, **kwargs):
    instance.profile.save()

post_save.connect(create_user_profile, sender=User)
post_save.connect(post_save_profile, sender=User)


class Verification_Code(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    method = models.CharField(max_length=10, choices=verification_methods)
    created_at = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=100, null=True, blank=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)
