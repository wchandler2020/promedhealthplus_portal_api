from rest_framework import serializers
from provider_auth.models import Profile, User
from patients.models import Patient
from orders.models import Order
from .models import SalesRep
from django.db.models import Count

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
    
    def get_patients(self, obj):
        try:
            # CORRECTED: Get the User instance from the Profile object
            user_instance = obj.user
            patients_queryset = user_instance.patients.all()
            return PatientSerializer(patients_queryset, many=True).data
        except User.DoesNotExist:
            return []

class SalesRepDashboardSerializer(serializers.ModelSerializer):
    providers = ProviderDashboardSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'providers', 'stats']

    def get_stats(self, obj):
        all_patients = Patient.objects.filter(provider__sales_reps=obj)
        all_orders = Order.objects.filter(patient__in=all_patients)

        stats = {
            'totalOrders': all_orders.count(),
            'deliveredOrders': all_orders.filter(status='Delivered').count(),
            'totalIVRs': all_patients.count(),
            'approvedIVRs': all_patients.filter(ivrStatus='Approved').count(),
        }

        orders_data = {}
        ivrs_data = {}

        for provider in obj.providers.all():
            provider_patients = all_patients.filter(provider=provider)
            provider_orders = all_orders.filter(patient__in=provider_patients)

            orders_data[provider.full_name] = {
                'total': provider_orders.count(),
                'delivered': provider_orders.filter(status='Delivered').count()
            }
            ivrs_data[provider.full_name] = {
                'total': provider_patients.count(),
                'approved': provider_patients.filter(ivrStatus='Approved').count()
            }

        stats['orders_data'] = orders_data
        stats['ivrs_data'] = ivrs_data
        
        return stats