from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    print('it gets to the azure media storage...')
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY
    azure_container = 'media'
    expiration_secs = None
    
class AzureStaticStorage(AzureStorage):
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY
    azure_container = "static" # <-- The container for static files
    expiration_secs = None