from onboarding_ops import models as api_models
from rest_framework import serializers
from onboarding_ops.pdf_utils import fill_pdf
from django.conf import settings
import uuid, os
from django.core.files.base import File
from patients.models import Patient
from .models import ProviderForm, provider_upload_path
from io import BytesIO
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from django.core.files.storage import default_storage
class ProviderFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.ProviderForm
        fields = '__all__'
        read_only_fields = ['user']
class ProviderDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    class Meta:
        model = api_models.ProviderDocument
        fields = ['id', 'document_type', 'file', 'file_url', 'uploaded_at']
        read_only_fields = ['user']

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file else None
    
class ProviderFormFillSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(write_only=True)
    form_type = serializers.CharField(write_only=True)
    form_data = serializers.DictField(write_only=True, required=False)
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        patient_id = validated_data.get('patient_id')
        form_type = validated_data.get('form_type')
        incoming_form_data = validated_data.get('form_data', {})

        try:
            patient = Patient.objects.get(id=patient_id, provider=user)
        except Patient.DoesNotExist:
            raise serializers.ValidationError({"error": "Patient not found or unauthorized."})

        # Pre-populate your default data here
        default_form_data = {
            # ... (your existing default data) ...
        }
        form_data = {**default_form_data, **incoming_form_data}
        now = datetime.now()
        timestamp = now.strftime('%m_%Y_%H-%M-%S')

        filename = f"{patient.first_name}_{patient.last_name}_{timestamp}_ivr_report.pdf"

        output_buffer = BytesIO()
        try:
            fill_pdf(form_type, form_data, output_buffer)
            output_buffer.seek(0)
        except Exception as e:
            raise serializers.ValidationError({"error": f"PDF generation failed: {str(e)}"})

        # --- CRITICAL FIX START ---
        # 1. Create and save the model instance to the database first.
        provider_form = ProviderForm.objects.create(
            user=user,
            patient=patient,
            form_type=form_type,
            completed=True,
            form_data=form_data
        )
        print("DEBUG: ProviderForm instance created, attempting to save file.")
        try:
            provider_form.completed_form.save(filename, File(output_buffer, name=filename))
            print("DEBUG: File save successful. It should be in Azure.")
        except Exception as e:
            print(f"DEBUG: File save failed: {e}")
            provider_form.delete() 
            raise serializers.ValidationError({"error": f"Azure upload failed: {str(e)}"})
    
        return provider_form

    def to_representation(self, instance):
        full_blob_path = instance.completed_form.name
        return {
            'form_id': instance.id,
            'completed_form_url': instance.completed_form.url,
            'completed_form_blob_path': full_blob_path,
            'form_data': instance.form_data,
        }
class ProviderFormUploadPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.ProviderForm
        fields = ['id', 'completed_form', 'form_data', 'date_created']
        read_only_fields = ['id', 'date_created']

    def create(self, validated_data):
        user = self.context['request'].user
        return api_models.ProviderForm.objects.create(user=user, **validated_data)

