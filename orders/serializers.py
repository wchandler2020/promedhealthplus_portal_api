from rest_framework import serializers
from .models import Order, OrderItem
from product.models import Product, ProductVariant
from patients.models import Patient


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())

    class Meta:
        model = OrderItem
        fields = ['product', 'variant', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'provider', 'status', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user

        order = Order.objects.create(
            provider=user,
            **validated_data
        )

        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                variant=item_data['variant'],
                quantity=item_data['quantity'],
            )

        return order

# ✅ 2. For displaying order history (no pricing)
class OrderItemDisplaySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'variant_name', 'quantity']

class OrderSummarySerializer(serializers.ModelSerializer):
    items = OrderItemDisplaySerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'created_at', 'status', 'items']  # ❌ No 'total' here

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
