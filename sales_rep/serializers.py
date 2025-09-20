# In your sales_rep/serializers.py file

from rest_framework import serializers
from provider_auth.models import Profile, User # Make sure to import User
from patients.models import Patient
from orders.models import Order
from .models import SalesRep
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at']
class PatientSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'ivrStatus', 'orders']
class ProviderDashboardSerializer(serializers.ModelSerializer):
    patients = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = ['id', 'full_name', 'patients']
    
    # Custom method to get the patients for this provider
    def get_patients(self, obj):
        try:
            user = User.objects.get(profile=obj)
            patients_queryset = user.patients.all()
            return PatientSerializer(patients_queryset, many=True).data
        except User.DoesNotExist:
            return []
class SalesRepDashboardSerializer(serializers.ModelSerializer):
    providers = ProviderDashboardSerializer(many=True, read_only=True)
    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'providers']