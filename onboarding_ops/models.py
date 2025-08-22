from django.db import models
from django.conf import settings
from provider_auth.models import User
from datetime import datetime
from patients.models import Patient
from django.utils.text import slugify
from promed_backend_api.storage_backends import AzureMediaStorage
# from utils.azure_storage import get_form_upload_path

import os
from django.utils.text import slugify

def provider_upload_path(instance, filename):
    now = datetime.now()
    timestamp = now.strftime('%m_%Y_%H-%M-%S')
    provider_name = slugify(getattr(instance.user, 'full_name', 'unknown-provider') or 'unknown-provider')
    patient_name = slugify(getattr(instance.patient, 'full_name', 'unknown-patient') or 'unknown-patient')
    # Ensure filename is safe
    base, ext = os.path.splitext(filename or 'file.pdf')
    safe_filename = f"{patient_name}_{timestamp}_{slugify(base)}{ext}"

    return f'providers/{provider_name}/{patient_name}/{safe_filename}'

class ProviderForm(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forms')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='forms', null=True, blank=True)
    form_type = models.CharField(max_length=100, blank=True, null=True)
    completed = models.BooleanField(default=False)
    completed_form = models.FileField(upload_to=provider_upload_path, null=True, blank=True)
    form_data = models.JSONField(null=True, blank=True)  # For in-portal completed form
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Form - {self.user.email} - {self.date_created.strftime("%Y-%m-%d")}'

class ProviderDocument(models.Model):
    DOCUMENT_TYPES = [
        ('BAA', 'Business Associate Agreement'),
        ('PURCHASE_AGREEMENT', 'Purchase Agreement'),
        ('MANUFACTURER_DOC', 'Manufacturer Onboarding Document'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=provider_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.document_type} - {self.user.email}'

