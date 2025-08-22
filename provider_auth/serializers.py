from .models import User, Profile
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        """
            Overrides the default get_token method to include additional user-specific
            data in the JWT payload. This method is called when a new token is generated
            (e.g., during user login).

            Args:
                user: The authenticated Django user object.

            Returns:
                A JWT token instance (a dictionary-like object) with custom claims added.
        """
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username

        # Return the modified token.
        return token

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'password2',)

    def validate(self, attr):
        if attr['password'] != attr['password2']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        return attr

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        if 'username' not in validated_data or not validated_data['username']:
            validated_data['username'] = validated_data['email'].split('@')[0] if '@' in validated_data['email'] else validated_data['email']

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        fields = ('id', 'email', 'full_name', 'username')

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer
    class Meta:
        model = Profile
        fields = '__all__'
        
class SendCodeSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=['email', 'sms'])

class VerifyCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    method = serializers.ChoiceField(choices=['email', 'sms'])


