# In your sales_rep/serializers.py file

from rest_framework import serializers
from provider_auth.models import Profile
from patients.models import Patient
from orders.models import Order
from .models import SalesRep

# Serializer for an individual Order
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at']

# Serializer for an individual Patient
class PatientSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'ivrStatus', 'orders']

# Serializer for an individual Provider (Profile)
class ProviderSerializer(serializers.ModelSerializer):
    # This correctly nests the Patient data using the PatientSerializer
    patients = PatientSerializer(many=True, read_only=True)
    class Meta:
        model = Profile
        fields = ['id', 'full_name', 'patients']

# The FINAL serializer that connects to the SalesRep model
class SalesRepDashboardSerializer(serializers.ModelSerializer):
    # This key field tells the serializer to use the ProviderSerializer
    # to handle the 'providers' relationship from the SalesRep model.
    providers = ProviderSerializer(many=True, read_only=True)
    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'providers']