from patients.models import Patient
from patients.serializers import PatientSerializer 
from .models import Order, OrderItem
from rest_framework import serializers
class OrderItemDisplaySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'variant_name', 'quantity']

class OrderSummarySerializer(serializers.ModelSerializer):
    items = OrderItemDisplaySerializer(many=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'items', 'total']

    def get_total(self, obj):
        total = Decimal(0)
        for item in obj.items.all():
            if item.variant:
                total += item.variant.price * item.quantity
        return total
class PatientOrderHistorySerializer(serializers.ModelSerializer):
    orders = serializers.SerializerMethodField()
    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'orders']

    def get_orders(self, obj):
        request = self.context.get('request')
        all_orders = request.query_params.get('all', 'false').lower() == 'true'
        qs = obj.orders.order_by('-created_at')
        if not all_orders:
            qs = qs[:5]
        return OrderSummarySerializer(qs, many=True).data
