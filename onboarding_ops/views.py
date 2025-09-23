from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


import requests
import os
import logging
from io import BytesIO

from patients.models import Patient
from provider_auth.models import User
from .models import ProviderForm, ProviderDocument
from .serializers import (
    ProviderFormSerializer,
    ProviderDocumentSerializer,
    JotFormWebhookSerializer,
    DocumentUploadSerializer
)
from utils.azure_storage import generate_sas_url
from azure.storage.blob import BlobServiceClient
from utils.azure_storage import upload_to_azure_stream

logger = logging.getLogger(__name__)

# Permissions
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

# CRUD Views for ProviderForm (kept as-is for management)
class ProviderFormListCreate(generics.ListCreateAPIView):
    serializer_class = ProviderFormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProviderForm.objects.filter(user=self.request.user)

class ProviderFormDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProviderFormSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return ProviderForm.objects.filter(user=self.request.user)

# --- JOTFORM WEBHOOK ---
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def jotform_webhook(request):
    """
    Handles Jotform webhook submissions. Downloads the PDF and saves it to Azure.
    """
    serializer = JotFormWebhookSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    form_data = data.get('content', {})
    provider_email = form_data.get('q4_providerEmail')  # Adjust to your Jotform field name
    form_name = data.get('formTitle', 'Jotform Submission')
    submission_id = data.get('submissionID')
    
    if not provider_email or not submission_id:
        logger.error("Jotform webhook missing required data.")
        return Response({"error": "Missing provider email or submission ID."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        provider = User.objects.get(email=provider_email)
    except User.DoesNotExist:
        logger.error(f"User with email {provider_email} not found.")
        return Response({"error": "Provider not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Download the PDF from Jotform
        pdf_url = form_data.get('submissionPDF', f"https://www.jotform.com/pdf-submission/{submission_id}")
        response = requests.get(pdf_url)
        response.raise_for_status()

        # Generate a clean, structured filename
        file_name = f"{slugify(form_name)}-{submission_id}.pdf"
        
        # Define the Azure blob path
        provider_slug = slugify(provider.full_name or 'unknown-provider')
        blob_path = f"media/{provider_slug}/onboard_documents/{file_name}"
        
        # Upload the file stream directly to Azure Blob Storage
        with BytesIO(response.content) as stream:
            upload_to_azure_stream(stream, blob_path, settings.AZURE_CONTAINER)
        
        # Create a database record
        form, created = ProviderForm.objects.get_or_create(
            user=provider,
            submission_id=submission_id,
            defaults={
                'form_type': form_name,
                'completed_form_path': blob_path,
                'form_data': form_data,
                'completed': True,
            }
        )
        if not created:
            # If the form already exists, update the path and data
            form.completed_form_path = blob_path
            form.form_data = form_data
            form.completed = True
            form.save()

        return Response({"success": True, "message": "Form processed and saved to Azure."}, status=status.HTTP_200_OK)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download PDF from Jotform: {e}")
        return Response({"error": "Failed to download PDF."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return Response({"error": f"Internal server error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DocumentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        doc_type = serializer.validated_data['document_type']
        uploaded_files = serializer.validated_data['files'] # This is now a list
        recipient_email = serializer.validated_data['recipient_email']
        user = request.user

        try:
            # Create a single email to send all files
            subject = f"New Documents from {user.full_name}"
            body = render_to_string('email/document_upload.html', {
                'user': user,
                'document_type': doc_type,
            })

            email = EmailMessage(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [recipient_email],
            )
            
            # Loop through the uploaded files and attach each one
            for uploaded_file in uploaded_files:
                email.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
            
            email.send()

            # Create a single record for the batch of documents
            # or create one for each document if you need to track them individually
            # Option 1: Create a single record
            ProviderDocument.objects.create(
                user=user,
                document_type=doc_type,
            )
            
            # Option 2: Create a record for each file
            # for uploaded_file in uploaded_files:
            #     ProviderDocument.objects.create(
            #         user=user,
            #         document_type=doc_type,
            #         # Maybe add a filename field to the model to track what was sent
            #     )

            return Response({"success": "Documents uploaded and emailed successfully."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Document upload/email failed: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# --- URL and Path Views (kept for existing functionality) ---
class GenerateSASURLView(APIView):
    # ... (Keep this view as it was, it's a good utility for getting a temporary URL)
    pass
class ServePDFFromAzure(APIView):
    # ... (Keep this view, it's used to serve the PDFs stored in Azure)
    pass