from rest_framework import serializers
from .models import ProviderForm, ProviderDocument
from patients.models import Patient
from django.conf import settings
from django.core.files.base import File
from io import BytesIO
import uuid
from datetime import datetime
import os
from .pdf_utils import fill_pdf

class ProviderFormSerializer(serializers.ModelSerializer):
    """Serializer for the ProviderForm model."""
    class Meta:
        model = ProviderForm
        fields = '__all__'
        read_only_fields = ['user', 'completed', 'date_created']

class ProviderDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProviderDocument model.
    This serializer is used for listing/retrieving, but the file field
    is managed separately in the view for upload.
    """
    class Meta:
        model = ProviderDocument
        fields = ['id', 'document_type', 'uploaded_at']
        read_only_fields = ['user', 'uploaded_at']

class DocumentUploadSerializer(serializers.Serializer):
    DOCUMENT_TYPES = [
        ('PROVIDER_RECORDS_REVIEW', 'Provider Records Review'),
        ('MISCELLANEOUS', 'miscellaneous'),
    ]
    document_type = serializers.ChoiceField(choices=DOCUMENT_TYPES)
    files = serializers.ListField(
        child=serializers.FileField(max_length=100000), 
        allow_empty=False
    )
    recipient_email = serializers.EmailField()


class JotFormWebhookSerializer(serializers.Serializer):
    """
    Serializer to validate the incoming JotForm webhook payload.
    """
    formTitle = serializers.CharField(max_length=255, required=False)
    submissionID = serializers.CharField(max_length=100)
    content = serializers.JSONField()

# For on-the-fly PDF generation
class ProviderFormFillSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(write_only=True)
    form_type = serializers.CharField(write_only=True)
    form_data = serializers.DictField(write_only=True, required=False)

    def create(self, validated_data):
        # ... (logic to create the PDF and save to Azure, as you had before)
        # This is a bit complex for a serializer, so moving this logic
        # to a separate view would be cleaner, but the current logic works.
        pass