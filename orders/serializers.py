from rest_framework import serializers
from product.models import Product, ProductVariant
from .models import OrderItem, Order
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all()) # Add this line

    class Meta:
        model = OrderItem
        fields = ['product', 'variant', 'quantity'] # Add 'variant' here

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'provider', 'total_price', 'status', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        total_price = Decimal('0.00')

        for item_data in items_data:
            product = item_data['product']
            variant = item_data['variant']  # Get the ProductVariant instance
            quantity = item_data['quantity']

            # Use the price from the selected ProductVariant
            price_at_order = variant.price * quantity 

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_order=price_at_order
            )
            total_price += price_at_order

        order.total_price = total_price
        order.save()
        return order