from rest_framework import serializers
from provider_auth.models import Profile, User
from patients.models import Patient
from orders.models import Order
from ivr.models import IVR  # Make sure to import the IVR model
from .models import SalesRep

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at']

class IVRSerializer(serializers.ModelSerializer):
    class Meta:
        model = IVR
        fields = ['id', 'status']

class PatientSerializer(serializers.ModelSerializer):
    orders = OrderSerializer(many=True, read_only=True)
    ivrs = IVRSerializer(many=True, read_only=True) # Add IVR serializer here

    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'orders', 'ivrs'] # Removed ivrStatus as it's not a field

class ProviderDashboardSerializer(serializers.ModelSerializer):
    patients = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = ['id', 'full_name', 'patients']
    
    def get_patients(self, obj):
        try:
            user = User.objects.get(profile=obj)
            patients_queryset = user.patients.all()
            return PatientSerializer(patients_queryset, many=True).data
        except User.DoesNotExist:
            return []

class StatSerializer(serializers.Serializer):
    totalOrders = serializers.IntegerField()
    deliveredOrders = serializers.IntegerField()
    totalIVRs = serializers.IntegerField()
    approvedIVRs = serializers.IntegerField()
    
    orders_data = serializers.DictField()
    ivrs_data = serializers.DictField()

class SalesRepDashboardSerializer(serializers.ModelSerializer):
    providers = ProviderDashboardSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'providers', 'stats']

    def get_stats(self, obj):
        all_patients = Patient.objects.filter(provider__sales_reps=obj)
        all_orders = Order.objects.filter(patient__in=all_patients)
        all_ivrs = IVR.objects.filter(patient__in=all_patients)

        stats = {
            'totalOrders': all_orders.count(),
            'deliveredOrders': all_orders.filter(status='Delivered').count(),
            'totalIVRs': all_ivrs.count(),
            'approvedIVRs': all_ivrs.filter(status='Approved').count(),
        }

        # Per-provider stats for charts
        orders_data = {}
        ivrs_data = {}

        for provider in obj.providers.all():
            provider_patients = all_patients.filter(provider=provider)
            provider_orders = all_orders.filter(patient__in=provider_patients)
            provider_ivrs = all_ivrs.filter(patient__in=provider_patients)

            orders_data[provider.full_name] = {
                'total': provider_orders.count(),
                'delivered': provider_orders.filter(status='Delivered').count()
            }
            ivrs_data[provider.full_name] = {
                'total': provider_ivrs.count(),
                'approved': provider_ivrs.filter(status='Approved').count()
            }

        stats['orders_data'] = orders_data
        stats['ivrs_data'] = ivrs_data
        
        return stats