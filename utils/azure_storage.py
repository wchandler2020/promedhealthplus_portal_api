from datetime import datetime, timedelta
from dotenv import load_dotenv
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions
)
import os
import re

def clean_string(s):
    return re.sub(r'\W+', '_', s)

load_dotenv()

AZURE_ACCOUNT_NAME = os.getenv('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.getenv('AZURE_ACCOUNT_KEY')

AZURE_CONTAINER = os.getenv('AZURE_CONTAINER') 


blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=AZURE_ACCOUNT_KEY
)

def generate_sas_url(blob_name: str, container_name: str, expiry_hours: int = 1) -> str:
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    if not blob_client.exists():
        raise FileNotFoundError(f"Blob '{blob_name}' not found in container '{container_name}'")
    
    sas_token = generate_blob_sas(
        account_name=AZURE_ACCOUNT_NAME,
        container_name=container_name,
        blob_name=blob_name,
        account_key=AZURE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
    )

    url = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
    return url

def provider_upload_path(instance, filename):
    provider_name = clean_string(instance.user.full_name)
    patient_name = clean_string(instance.patient.full_name) if instance.patient else "unknown_patient"
    return f'{provider_name}/{patient_name}/{filename}'