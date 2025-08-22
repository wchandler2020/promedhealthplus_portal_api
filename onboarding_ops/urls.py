
from django.urls import path
from onboarding_ops import views as api_views

urlpatterns = [
    # Provider Forms
    path('forms/', api_views.ProviderFormListCreate.as_view(), name='provider-form-list'),
    path('forms/fill/', api_views.FillPreexistingPDF.as_view(), name='provider-form-list'),
    path('forms/upload/', api_views.UploadFilledPDF.as_view(), name='upload-filled-pdf'),
    path('forms/<int:pk>/', api_views.ProviderFormDetail.as_view(), name='provider-form-detail'),
    path('forms/blank/<str:form_type>/', api_views.serve_blank_form, name='serve-blank-form'),
    
    # Provider Documents
    path('documents/', api_views.ProviderDocumentListCreate.as_view(), name='provider-document-list'),
    path('documents/<int:pk>/', api_views.ProviderDocumentDetail.as_view(), name='provider-document-detail'),
    
    # New URLs for prepopulating forms
    path('forms/prepopulate/', api_views.ServeFilledPDFOnTheFly.as_view(), name='prepopulate-form'),
    path('forms/prepopulate-data/', api_views.GetPrepopulatedFormData.as_view(), name='get-prepopulated-data'),
    path('forms/prepopulate-and-serve/', api_views.PrepopulateAndServeWithUserData.as_view(), name='prepopulate-and-serve'),
    
    # Create SSL for blob storage
    # path('forms/sas-url/<str:blob_name>/', api_views.GenerateSASURLView.as_view(), name='get_pdf_sas_url'),
    path('forms/sas-url/<str:container_name>/<path:blob_name>/', api_views.GenerateSASURLView.as_view(), name='generate-sas-url'),
    path('forms/serve/<str:blob_name>/', api_views.ServePDFFromAzure.as_view(), name='serve-pdf'), 
    path('forms/check-blob/<str:container_name>/<path:blob_name>/', api_views.CheckBlobExistsView.as_view(), name='check-blob-exists'),
]