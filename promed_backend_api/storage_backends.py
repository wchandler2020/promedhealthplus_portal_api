from storages.backends.azure_storage import AzureStorage
from django.conf import settings

class AzureMediaStorage(AzureStorage):
    # Move the setting access into the class or a method
    def __init__(self, *args, **kwargs):
        # Access settings here, where they are guaranteed to be loaded
        self.account_name = settings.AZURE_ACCOUNT_NAME
        self.account_key = settings.AZURE_ACCOUNT_KEY
        self.azure_container = settings.AZURE_CONTAINER
        self.overwrite_files = True
        self.location = settings.MEDIA_URL.replace(f'https://{self.account_name}.blob.core.windows.net/', '')
        super().__init__(*args, **kwargs)

class AzureStaticStorage(AzureStorage):
    def __init__(self, *args, **kwargs):
        self.account_name = settings.AZURE_ACCOUNT_NAME
        self.account_key = settings.AZURE_ACCOUNT_KEY
        self.azure_container = settings.AZURE_CONTAINER
        self.overwrite_files = True
        self.location = settings.STATIC_URL.replace(f'https://{self.account_name}.blob.core.windows.net/', '')
        super().__init__(*args, **kwargs)