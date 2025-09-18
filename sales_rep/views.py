from rest_framework import generics, permissions, status
from rest_framework.response import Response
from provider_auth.models import Profile, User
from patients.models import Patient
from patients.serializers import PatientSerializer

class SalesRepDashboardView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PatientSerializer

    def get_queryset(self):
        user = self.request.user # The user object is available here
        
        # Check the role directly from the user object
        if user.role != 'sales_rep':
            return Patient.objects.none()
        
        # If the user is a sales rep, filter the data accordingly
        try:
            sales_rep_profile = user.profile
            sales_rep = sales_rep_profile.sales_rep
        except (Profile.DoesNotExist, AttributeError):
            return Patient.objects.none()

        if not sales_rep:
            return Patient.objects.none()

        provider_profiles = Profile.objects.filter(sales_rep=sales_rep)
        provider_user_ids = [profile.user.id for profile in provider_profiles]
        
        return Patient.objects.filter(provider__id__in=provider_user_ids)