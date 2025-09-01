from rest_framework import serializers
from product.models import Product
from .models import OrderItem, Order
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    # Use PrimaryKeyRelatedField for the product, as the client will send the product ID
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

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
            product = item_data['product']  # Get the Product instance from the validated data
            quantity = item_data['quantity']
            price_at_order = product.mft_price * quantity # Calculate the total price for the item

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