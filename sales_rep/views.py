# sales_rep/views.py
from rest_framework import generics, permissions
from rest_framework.response import Response
from provider_auth.models import Profile, User
from patients.models import Patient
from patients.serializers import PatientSerializer  # Make sure this exists!

class SalesRepDashboardView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PatientSerializer  # Set your serializer here

    def get_queryset(self):
        user = self.request.user

        # Only allow sales reps
        if user.role != 'sales_rep':
            return Patient.objects.none()

        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return Patient.objects.none()

        sales_rep = profile.sales_rep
        if not sales_rep:
            return Patient.objects.none()

        # Get providers linked to this sales rep
        provider_user_ids = sales_rep.providers.values_list('user__id', flat=True)

        # Return patients whose provider is one of those users
        return Patient.objects.filter(provider__id__in=provider_user_ids)
