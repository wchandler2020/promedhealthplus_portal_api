#auth_user.serializers
from .models import User, Profile, COUNTRY_CODE_CHOICES
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import auth
from orders.models import Order, OrderItem

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        # Add new fields to the token
        token['phone_number'] = str(user.phone_number) if user.phone_number else None
        token['country_code'] = user.country_code
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = auth.authenticate(
            request=self.context.get('request'),
            email=attrs['email'],
            password=attrs['password']
        )
        if user and not user.is_verified:
            raise serializers.ValidationError({"detail": "Email not verified. Please check your inbox for a verification link."})
        return data

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    # Define a serializer field for the country code choices
    country_code = serializers.ChoiceField(choices=COUNTRY_CODE_CHOICES, required=False)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'phone_number', 'country_code', 'password', 'password2')
        extra_kwargs = {
            'phone_number': {'required': False},
            'country_code': {'required': False},
        }

    def validate(self, attr):
        if attr['password'] != attr['password2']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        return attr

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')

        # Pop the new fields
        phone_number = validated_data.pop('phone_number', None)
        country_code = validated_data.pop('country_code', None)

        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email'].split('@')[0] if '@' in validated_data['email'] else validated_data['email']

        user = User.objects.create(
            phone_number=phone_number,
            country_code=country_code,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'username', 'phone_number', 'country_code')

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = '__all__'

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

class SendCodeSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'sms'])

class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    method = serializers.ChoiceField(choices=['email', 'sms'])

class ContactRepSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    message = serializers.CharField(required=True)
    
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'manufacturer', 'quantity', 'mft_price']
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'provider', 'total_price', 'status', 'created_at']  # fixed 'total_price' typo

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)  # <- FIXED TYPO here
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order
