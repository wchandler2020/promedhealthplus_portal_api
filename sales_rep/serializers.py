from rest_framework import serializers
from provider_auth.models import Profile
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
    patients = PatientSerializer(many=True, read_only=True)
    class Meta:
        model = Profile
        fields = ['id', 'full_name', 'patients']
class SalesRepDashboardSerializer(serializers.ModelSerializer):
    providers = ProviderDashboardSerializer(many=True, read_only=True)
    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'providers']