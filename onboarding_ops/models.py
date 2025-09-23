# onboarding_ops/models.py
from django.db import models
from django.conf import settings
from patients.models import Patient
from django.utils.text import slugify
from datetime import datetime
import uuid
import os

# Moved this import to the top
from provider_auth.models import User

# === REFACTORED PATH FUNCTIONS ===
def provider_form_upload_path(instance, filename):
    """Dynamically generates the upload path for ProviderForm instances."""
    provider_name = slugify(getattr(instance.user, 'full_name', 'unknown-provider') or 'unknown-provider')
    
    # Use the form_type and submission_id to create a unique and descriptive filename.
    form_type = slugify(getattr(instance, 'form_type', 'onboarding-form'))
    submission_id = getattr(instance, 'submission_id', 'no-id')
    
    base, ext = os.path.splitext(filename or 'file.pdf')
    unique_filename = f"{form_type}_{submission_id}_{uuid.uuid4().hex[:8]}{ext}"
    
    # Path: media/provider_name/onboarding/forms/form_type/filename.pdf
    return f'media/{provider_name}/onboarding/forms/{form_type}/{unique_filename}'

def provider_document_upload_path(instance, filename):
    """Dynamically generates the upload path for ProviderDocument instances."""
    provider_name = slugify(getattr(instance.user, 'full_name', 'unknown-provider') or 'unknown-provider')
    document_type = slugify(instance.document_type)

    base, ext = os.path.splitext(filename or 'file')
    unique_filename = f"{document_type}_{uuid.uuid4().hex[:8]}{ext}"
    
    # Path: media/provider_name/onboarding/documents/document_type/filename.ext
    return f'media/{provider_name}/onboarding/documents/{document_type}/{unique_filename}'

# === REFACTORED MODELS ===
class ProviderForm(models.Model):
    """Model to store completed forms, either filled via the portal or submitted via Jotform."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_forms')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, related_name='patient_forms', null=True, blank=True)
    form_type = models.CharField(max_length=100, help_text="e.g., 'New Account Form', 'IVR Report'")
    submission_id = models.CharField(max_length=255, unique=True, null=True, blank=True,
                                     help_text="Unique ID from an external system like Jotform.")
    completed_form = models.FileField(upload_to=provider_form_upload_path, null=True, blank=True,
                                      help_text="The completed PDF file.")
    form_data = models.JSONField(null=True, blank=True,
                                 help_text="Snapshot of the form's data at the time of submission.")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.form_type} for {self.user.email} on {self.date_created.strftime("%Y-%m-%d")}'

    class Meta:
        verbose_name = "Provider Form"
        verbose_name_plural = "Provider Forms"
        ordering = ['-date_created']

class ProviderDocument(models.Model):
    """Model to store a provider's supporting documents like agreements and licenses."""
    DOCUMENT_TYPES = [
        ('PROVIDER_REVIEW_DOC', 'Provider Review Request Docs'),
        ('OTHER', 'Other')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES,
                                     help_text="Type of document, e.g., BAA, License.")
    file = models.FileField(upload_to=provider_document_upload_path,
                            help_text="The uploaded document file.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.document_type} - {self.user.full_name}'

    class Meta:
        verbose_name = "Provider Document"
        verbose_name_plural = "Provider Documents"
        ordering = ['-uploaded_at']