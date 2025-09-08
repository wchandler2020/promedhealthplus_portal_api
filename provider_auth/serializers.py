from .models import User, Profile, COUNTRY_CODE_CHOICES
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import auth
from django.core.exceptions import ValidationError
from orders.models import Order, OrderItem
from product.models import Product
from decimal import Decimal

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
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
    npi_number = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'phone_number', 'password', 'password2', 'npi_number')
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True},
            'full_name': {'required': True},
            'npi_number': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        try:
            data = validated_data.copy()
            
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                full_name=data['full_name'],
                phone_number=data['phone_number'],
                npi_number=data['npi_number'],
                password=data['password']
            )
            return user
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
    class Meta:
        model = User
        fields = ["full_name", "email", "phone_number", "password", "password2", "npi_number"]

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        npi_number = attrs.get('npi_number')
        if npi_number and len(npi_number) != 10:
            raise serializers.ValidationError({"npi_number": "NPI number must be 10 digits."})
            
        return attrs

    def create(self, validated_data):
        try: 
            data = validated_data.copy()        
            user = User.objects.create_user(
                    username=data['email'], # <--- Add this line
                    email=data['email'],
                    full_name=data['full_name'],
                    phone_number=data['phone_number'],
                    npi_number=data['npi_number'],
                    password=data['password']
            )
            return user
        except  as e:
            
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
    
class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
