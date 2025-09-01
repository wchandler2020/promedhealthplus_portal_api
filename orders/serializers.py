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

        total_price = Decimal('0.00')  # ← Calculate total before saving

        # Temporarily hold order item instances
        order_items = []

        for item_data in items_data:
            product = item_data['product']
            variant = item_data['variant']
            quantity = item_data['quantity']

            price_at_order = variant.price * quantity
            total_price += price_at_order

            order_items.append({
                'product': product,
                'variant': variant,
                'quantity': quantity,
                'price_at_order': price_at_order
            })

        # Now we have the total_price — create the order
        order = Order.objects.create(
            **validated_data,
            total_price=total_price  # ✅ explicitly set
        )

        # Save order items
        for item in order_items:
            OrderItem.objects.create(order=order, **item)

        return order
