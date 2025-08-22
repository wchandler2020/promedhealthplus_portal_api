import random
import uuid

from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from .models import User, Profile
from provider_auth import models as api_models
from provider_auth import serializers as api_serializers
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
from twilio.rest import Client
from django.core.mail import send_mail
from dotenv import load_dotenv
import random
import os

load_dotenv()
# k_phone = os.getenv('KAYVON_PHONE_NUMBER')

# Create your views here.
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializers.MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        # Issue tokens immediately
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        # Create MFA code and send it
        method = request.data.get('method', 'email')
        code = str(random.randint(100000, 999999))
        session_id = str(uuid.uuid4())
        twilio_api_key = os.getenv('TWILIO_API_KEY')
        twilio_secret_key = os.getenv('TWILIO_SECRET_KEY')
        api_models.Verification_Code.objects.create(user=user, code=code, method=method, session_id=session_id)
        # Send code via email or SMS
        phone_number = '+15022633992'  # Replace with user's phone number
        if method == 'sms':
            client = Client(twilio_api_key, twilio_secret_key)
            client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                to=phone_number,
                channel='sms'
            )
        elif method == 'email':
            send_mail(
                subject='Login Verification Code',
                message=f'Your code is {code}',
                from_email='noreply@example.com',
                recipient_list=[user.email]
            )
        request.session['mfa'] = False  # Mark session as requiring MFA
        return Response({
            'access': str(access),
            'refresh': str(refresh),
            'mfa_required': True,
            'session_id': session_id,
            'detail': 'Verification code sent.'
        }, status=status.HTTP_200_OK)

class RegisterUser(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = api_serializers.RegisterSerializer
     
class VerifyCodeView(generics.CreateAPIView):
    serializer_class = api_serializers.VerifyCodeSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        # Require JWT authentication
        user = request.user
        session_id = request.data.get('session_id')
        code = request.data.get('code')
        twilio_api_key = os.getenv('TWILIO_API_KEY')
        twilio_secret_key = os.getenv('TWILIO_SECRET_KEY')
        if not user or not session_id or not code:
            return Response({'error': 'Missing data'}, status=status.HTTP_400_BAD_REQUEST)
        # Check code
        valid_code = api_models.Verification_Code.objects.filter(
            session_id=session_id,
        ).order_by('-created_at').first()
        if not valid_code:
            return Response({'verified': False, 'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)
        # Mark user as verified
        phone_number = '+15022633992'  # Replace with user's phone
        client = Client(twilio_api_key, twilio_secret_key)
        verification_check = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
        to=phone_number,
        code=code)
        if not verification_check.valid:
            return Response({'verified': False, 'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)
        request.session['mfa'] = True  # Mark session as verified
        return Response({'verified': True}, status=status.HTTP_200_OK)

class ProviderProfileView(generics.RetrieveAPIView):
    serializer_class = api_serializers.ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile
    
    def put(self, request, *args, **kwargs):
        profile = self.get.object()
        serializer = self.serializer_class(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# provider_auth/views.py

# ... (other imports and views) ...

class ContactRepView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile

        if not profile.sales_rep:
            return Response(
                {'error': 'No sales representative assigned to this provider.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sales_rep = profile.sales_rep
        rep_email = sales_rep.email
        rep_name = sales_rep.name
        print(user.email)

        sender_name = request.data.get('name', user.full_name)
        sender_phone = request.data.get('phone', user.phone_number)
        sender_email = request.data.get('email', user.email)
        message_body = request.data.get('message')

        if not message_body:
            return Response(
                {'error': 'Message body is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject = f"New Message from Provider: {sender_name}"
        email_message = (
            f"Hello {rep_name},\n\n"
            f"You have a new message from a provider on the ProMed Health Plus Portal.\n\n"
            f"**Provider Details:**\n"
            f"Name: {sender_name}\n"
            f"Email: {sender_email}\n"
            f"Phone: {sender_phone}\n\n"
            f"**Message:**\n"
            f"{message_body}\n\n"
            f"Please respond to the provider at your earliest convenience."
        )

        try:
            # Create a set to automatically remove duplicates, then convert back to a list
            recipient_list = list(set([
                rep_email,
                'william.d.chandler1@gmail.com', 
                'harold@promedhealthplus.com', 
                'kayvoncrenshaw@gmail.com',
                'william.dev@promedhealthplus.com'
            ]))

            send_mail(
                subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )
            return Response(
                {'success': 'Message sent successfully.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            return Response(
                {'error': 'Failed to send message via email.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    