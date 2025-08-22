from django.urls import path
from patients import views as api_views
urlpatterns = [
    path('patients/', api_views.PatientListView.as_view(), name='patient-list'),
]
