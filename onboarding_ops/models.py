# onboarding_ops/models.py

from django.db import models
from django.conf import settings
from provider_auth.models import User
from patients.models import Patient
from django.utils.text import slugify
from promed_backend_api.storage_backends import AzureMediaStorage
import uuid
import os
from datetime import datetime

def provider_upload_path(instance, filename):
    now = datetime.now()
    timestamp = now.strftime('%Y_%m_%d_%H%M%S') # Use a more detailed timestamp
    
    # Get provider name. Slugify for clean URLs.
    provider_name = slugify(getattr(instance.user, 'full_name', 'unknown-provider') or 'unknown-provider')

    # Get the form type from the instance
    form_type = slugify(getattr(instance, 'form_type', 'onboarding_file'))

    # The final path structure: media/provider_name/onboarding_files/file.pdf
    # This matches your desired structure
    base, ext = os.path.splitext(filename or 'file.pdf')
    unique_filename = f"{form_type}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
    
    return f'media/{provider_name}/onboarding_files/{unique_filename}'

def document_upload_path(instance, filename):
    # This function is correct for your `ProviderDocument` model.
    provider_name = slugify(getattr(instance.user, 'full_name', 'unknown-provider') or 'unknown-provider')
    base, ext = os.path.splitext(filename or 'file')
    unique_filename = f"{slugify(base)}_{uuid.uuid4().hex}{ext}"
    return f'providers/{provider_name}/intake_files/{unique_filename}'


class ProviderForm(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forms')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='forms', null=True, blank=True)
    form_type = models.CharField(max_length=100, blank=True, null=True)
    completed = models.BooleanField(default=False)
    # New field to store the unique JotForm submission ID
    submission_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    completed_form = models.FileField(upload_to=provider_upload_path, null=True, blank=True)
    form_data = models.JSONField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Form - {self.user.email} - {self.form_type} ({self.date_created.strftime("%Y-%m-%d")})'

class ProviderDocument(models.Model):
    DOCUMENT_TYPES = [
        ('BAA', 'Business Associate Agreement'),
        ('PURCHASE_AGREEMENT', 'Purchase Agreement'),
        ('MANUFACTURER_DOC', 'Manufacturer Onboarding Document'),
        ('PROVIDER_REVIEW_DOC', 'Provider Review Request Docs'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.document_type} - {self.user.email}'