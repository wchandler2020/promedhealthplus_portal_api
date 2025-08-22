from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from onboarding_ops import models as api_models
from onboarding_ops import serializers as api_serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, HttpResponseNotFound, StreamingHttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from .pdf_utils import fill_pdf, fetch_pdf_template_from_azure, TEMPLATE_BLOB_NAMES

from patients.models import Patient
from .models import ProviderForm
from utils.azure_storage import generate_sas_url
from azure.storage.blob import BlobServiceClient
from django.conf import settings
import requests
import uuid
import os
import json
from io import BytesIO

# Permissions
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

# CRUD Views for ProviderForm
class ProviderFormListCreate(generics.ListCreateAPIView):
    serializer_class = api_serializers.ProviderFormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return api_models.ProviderForm.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProviderFormDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.ProviderFormSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return api_models.ProviderForm.objects.filter(user=self.request.user)

# CRUD Views for ProviderDocument
class ProviderDocumentListCreate(generics.ListCreateAPIView):
    serializer_class = api_serializers.ProviderDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return api_models.ProviderDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProviderDocumentDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.ProviderDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return api_models.ProviderDocument.objects.filter(user=self.request.user)

# Mark form as completed
class ProviderFormComplete(generics.UpdateAPIView):
    serializer_class = api_serializers.ProviderFormSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    http_method_names = ['patch']

    def get_queryset(self):
        return api_models.ProviderForm.objects.filter(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        request.data['completed'] = True
        return super().partial_update(request, *args, **kwargs)

# Upload filled PDF (Azure upload handled elsewhere)
class UploadFilledPDF(generics.CreateAPIView):
    serializer_class = api_serializers.ProviderFormUploadPDFSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return api_models.ProviderForm.objects.filter(user=self.request.user)

# Context injector for serializer
class FillPreexistingPDF(generics.CreateAPIView):
    serializer_class = api_serializers.ProviderFormFillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {'request': self.request}

# Serve blank form template from Azure
@xframe_options_exempt
def serve_blank_form(request, form_type):
    blob_name = TEMPLATE_BLOB_NAMES.get(form_type)
    if not blob_name:
        return HttpResponseNotFound("Form type not recognized.")

    try:
        pdf_stream = fetch_pdf_template_from_azure(blob_name)
        return FileResponse(pdf_stream, content_type='application/pdf')
    except FileNotFoundError:
        return HttpResponseNotFound("Template not found in Azure.")
    
class GenerateSASURLView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'blob_name'

    def retrieve(self, request, *args, **kwargs):
        # Capture the blob_name and container_name from the URL
        blob_name = kwargs.get(self.lookup_url_kwarg)
        container_name = kwargs.get('container_name')

        # Strip any trailing slashes from the blob_name.
        # This is a crucial step to ensure the name matches the blob in Azure.
        if blob_name and blob_name.endswith('/'):
            blob_name = blob_name.rstrip('/')
        
        if not blob_name or not container_name:
            raise NotFound("Container name or blob name not provided.")

        try:
            # Pass the corrected blob_name and container_name to the utility function
            sas_url = generate_sas_url(blob_name, container_name)
            return Response({"sas_url": sas_url})
        except FileNotFoundError:
            # Return a 404 for a specific "file not found" case
            return Response({"error": f"Blob '{blob_name}' not found in container '{container_name}'"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Catch other potential errors and return a 500
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Stream PDF directly from Azure blob using SAS
class ServePDFFromAzure(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        blob_name = kwargs.get('blob_name')
        if not blob_name:
            return Response({"error": "Blob name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # This line is crucial for correctly locating the file in Azure.
        # It's needed to handle the pathing correctly.
        blob_name = os.path.basename(blob_name.strip("/"))
        
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_CONTAINER)

        try:
            blob_client = container_client.get_blob_client(blob_name)

            if not blob_client.exists():
                # Fallback logic if primary blob not found
                form_type_parts = blob_name.replace(".pdf", "").split("_")
                if "IVR" in form_type_parts:
                    fallback_blob_name = "promed_healthcare_plus_ivr_blank.pdf"
                else:
                    return HttpResponseNotFound("Filled form and fallback blank form not found.")

                blob_client = container_client.get_blob_client(fallback_blob_name)
                if not blob_client.exists():
                    return HttpResponseNotFound("Fallback form not found in Azure.")

                blob_name = fallback_blob_name

            # Stream blob via temporary signed URL
            sas_url = generate_sas_url(blob_name)
            response = requests.get(sas_url, stream=True)
            response.raise_for_status()

            resp = StreamingHttpResponse(
                streaming_content=response.iter_content(chunk_size=8192),
                content_type='application/pdf'
            )
            resp['Content-Disposition'] = f'inline; filename="{os.path.basename(blob_name)}"'
            resp['X-Frame-Options'] = 'ALLOWALL'
            return resp

        except Exception as e:
            return Response(
                {"error": f"Failed to fetch PDF from Azure: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class ServeFilledPDFOnTheFly(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        patient_id = request.query_params.get('patient_id')
        form_type = request.query_params.get('form_type')
        user = request.user

        if not patient_id or not form_type:
            return Response({"error": "Patient ID and form type are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=patient_id, provider=user)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)

        # Build the prepopulated data dictionary
        default_form_data = {
            'Provider Name': user.full_name,
            'Text38': user.email,
            'Text56': patient.address,
            'Text59': str(patient.date_of_birth),
            'Text57': str(patient.phone_number),
            'Text62': patient.primary_insurance,
            'Text63': patient.primary_insurance_number,
            'Text65': patient.secondary_insurance,
            'Text66': patient.secondary_insurance_number,
            'PATIENT ADDRESS': patient.address,
            'Text60': f'{patient.city}, {patient.state} {patient.zip_code}',
            'PATIENT PHONE': str(patient.phone_number),
            'PATIENT FAX/EMAIL': patient.email,
        }

        output_buffer = BytesIO()

        try:
            # Fill the PDF in memory
            fill_pdf(form_type, default_form_data, output_buffer)
            output_buffer.seek(0)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except FileNotFoundError as fnfe:
            return HttpResponseNotFound(str(fnfe))
        except Exception as e:
            return Response({"error": f"PDF generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Stream the filled PDF back to the client
        response = StreamingHttpResponse(output_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{patient.first_name}_{patient.last_name}_{form_type}.pdf"'
        response['X-Frame-Options'] = 'ALLOWALL'
        return response
    
class PrepopulateAndServeWithUserData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        patient_id = request.data.get('patient_id')
        form_type = request.data.get('form_type')
        user_submitted_data = request.data.get('form_data', {})
        
        if not isinstance(user_submitted_data, dict):
            return Response({"error": "form_data must be a dictionary."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if not patient_id or not form_type:
            return Response({"error": "Patient ID and form type are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=patient_id, provider=user)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)

        default_form_data = {
            'Provider Name': user.full_name,
            'Text38': user.email,
            'Text56': patient.address,
            'Text59': str(patient.date_of_birth),
            'Text57': str(patient.phone_number),
            'Text62': patient.primary_insurance,
            'Text63': patient.primary_insurance_number,
            'Text65': patient.secondary_insurance,
            'Text66': patient.secondary_insurance_number,
            'PATIENT ADDRESS': patient.address,
            'Text60': f'{patient.city}, {patient.state} {patient.zip_code}',
            'PATIENT PHONE': str(patient.phone_number),
            'PATIENT FAX/EMAIL': patient.email,
        }

        # Merge form fields
        merged_data = {**default_form_data, **user_submitted_data}

        output_buffer = BytesIO()
        try:
            fill_pdf(form_type, merged_data, output_buffer)
            output_buffer.seek(0)
        except Exception as e:
            return Response({"error": f"PDF generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response = StreamingHttpResponse(output_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="prepopulated_form.pdf"'
        response['X-Frame-Options'] = 'ALLOWALL'
        return response
            
class GetPrepopulatedFormData(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        patient_id = request.query_params.get('patient_id')
        user = request.user
        
        if not patient_id:
            return Response({"error": "Patient ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id, provider=user)
        except ObjectDoesNotExist:
            return Response({"error": "Patient not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)
        
        # Build and return the pre-populated data dictionary
        default_form_data = {
            'Provider Name': user.full_name,
            'Text38': user.email,
            'Text56': patient.address,
            'Text59': str(patient.date_of_birth),
            'Text57': str(patient.phone_number),
            'Text62': patient.primary_insurance,
            'Text63': patient.primary_insurance_number,
            'Text65': patient.secondary_insurance,
            'Text66': patient.secondary_insurance_number,
            'PATIENT ADDRESS': patient.address,
            'Text60': f'{patient.city}, {patient.state} {patient.zip_code}',
            'PATIENT PHONE': str(patient.phone_number),
            'PATIENT FAX/EMAIL': patient.email,
        }
        
        return Response(default_form_data, status=status.HTTP_200_OK)

class CheckBlobExistsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, container_name, blob_name, *args, **kwargs):
        try:
            blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            exists = blob_client.exists()
            return Response({"exists": exists}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


