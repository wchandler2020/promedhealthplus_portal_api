from rest_framework import serializers
from product.models import Product, ProductVariant
from .models import OrderItem, Order
from decimal import Decimal
class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    class Meta:
        model = OrderItem
        fields = ['product', 'variant', 'quantity']  # no price here
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'provider', 'status', 'created_at']  # no total_price here

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


