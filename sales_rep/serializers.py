from collections import defaultdict
from orders.models import Order
from patients.models import Patient

class SalesRepDashboardSerializer(serializers.ModelSerializer):
    providers = ProviderDashboardSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = SalesRep
        fields = ['id', 'name', 'providers', 'stats']

    def get_stats(self, obj):
        provider_stats = []
        for provider in obj.providers.all():
            user = provider.user  # assuming `Profile` is linked to `User`
            patients = user.patients.all()
            total_orders = delivered_orders = total_ivrs = approved_ivrs = 0

            for patient in patients:
                orders = patient.orders.all()
                total_orders += orders.count()
                delivered_orders += orders.filter(status="Delivered").count()

                total_ivrs += len(patient.ivrStatus)
                approved_ivrs += sum(1 for ivr in patient.ivrStatus if ivr.get("status") == "Approved")

            provider_stats.append({
                "provider_id": provider.id,
                "provider_name": provider.full_name,
                "total_orders": total_orders,
                "delivered_orders": delivered_orders,
                "total_ivrs": total_ivrs,
                "approved_ivrs": approved_ivrs,
            })

        return {
            "by_provider": provider_stats
        }
