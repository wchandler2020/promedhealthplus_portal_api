import random
import uuid

from django.shortcuts import render
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives, EmailMessage
from .models import User, Profile, EmailVerificationToken
from orders.models import Order, OrderItem
from provider_auth import models as api_models
from provider_auth import serializers as api_serializers
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from decimal import Decimal
from twilio.rest import Client
from django.core.mail import send_mail
from dotenv import load_dotenv
from django.template.loader import render_to_string
from datetime import datetime
from weasyprint import HTML
from io import BytesIO
from promed_backend_api.settings import LOCAL_HOST, DEFAULT_FROM_EMAIL
import random
import os

load_dotenv()
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializers.MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        method = request.data.get('method', 'email')
        code = str(random.randint(100000, 999999))
        session_id = str(uuid.uuid4())
        twilio_api_key = os.getenv('TWILIO_API_KEY')
        twilio_secret_key = os.getenv('TWILIO_SECRET_KEY')
        api_models.Verification_Code.objects.create(user=user, code=code, method=method, session_id=session_id)

        # Add a check to see if the user has a phone number
        if user.phone_number:
            phone_number = str(user.phone_number)
            print('Phone number: ', phone_number)
            if method == 'sms':
                client = Client(twilio_api_key, twilio_secret_key)
                client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                    to=phone_number,
                    channel='sms'
                )

        # Continue with email logic regardless of phone number
        if method == 'email':
            send_mail(
                subject='Login Verification Code',
                message=f'Your code is {code}',
                from_email = settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email]
            )

        request.session['mfa'] = False

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
    def perform_create(self, serializer):
        user = serializer.save()
        token, created = EmailVerificationToken.objects.get_or_create(user=user)

        verification_link = f"https://wchandler2020.github.io/promedhealthplus_portal_client/#/verify-email/{token.token}"
        
        email_html_message = render_to_string(
            'provider_auth/email_verification.html',
            {
                'user': user,
                'verification_link': verification_link
            }
        )
        send_mail(
            subject='Verify Your Email Address',
            message=f"Click the link to verify your email: {verification_link}",
            html_message=email_html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        try:
            verification_token = EmailVerificationToken.objects.get(token=token)
            user = verification_token.user
            if user.is_verified:
                return Response({"message": "Email already verified."}, status=status.HTTP_200_OK)

            user.is_verified = True
            user.save()
            verification_token.delete()
            # Send welcome email
            welcome_html = render_to_string(
                'provider_auth/welcome_email.html',
                {'user': user}
            )

            send_mail(
                subject='Welcome to ProMed Health Plus!',
                message='Welcome to ProMed Health Plus! We are excited to have you on board.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=welcome_html,
                fail_silently=False
            )
            return Response({"message": "Email successfully verified. You can now log in."}, status=status.HTTP_200_OK)

        except EmailVerificationToken.DoesNotExist:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

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
        phone_number = str(user.phone_number)
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
        profile = self.get_object()
        serializer = self.serializer_class(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ContactRepView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = api_serializers.ContactRepSerializer

    def create(self, request, *args, **kwargs):
        if getattr(self, 'swagger_fake_view', False):  # Prevent drf_yasg crash
            return Response(status=status.HTTP_200_OK)

        user = request.user

        profile = getattr(user, 'profile', None)
        if not profile or not profile.sales_rep:
            return Response(
                {'error': 'No sales representative assigned to this provider.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract data
        sales_rep = profile.sales_rep
        rep_email = sales_rep.email
        rep_name = sales_rep.name

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

        # Render HTML email template
        html_message = render_to_string('provider_auth/provider_inquiry.html', {
            'rep_name': rep_name,
            'sender_name': sender_name,
            'sender_email': sender_email,
            'sender_phone': sender_phone,
            'message_body': message_body,
            'year': datetime.now().year
        })

        recipient_list = list(set([
            rep_email,
            'william.d.chandler1@gmail.com',
            'harold@promedhealthplus.com',
            'kayvoncrenshaw@gmail.com',
            'william.dev@promedhealthplus.com'
        ]))

        try:
            send_mail(
                subject=subject,
                message=message_body,  # plain-text fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            return Response({'success': 'Message sent successfully.'}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error sending provider inquiry email: {e}")
            return Response(
                {'error': 'Failed to send message via email.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
class ResetPasswordView(generics.GenericAPIView):
    serializer_class = api_serializers.ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            reset_token = api_models.PasswordResetToken.objects.get(token=token)
        except api_models.PasswordResetToken.DoesNotExist:
            return Response({'error': 'Invalid or expired token.'}, status=400)

        if reset_token.is_expired():
            reset_token.delete()
            return Response({'error': 'Token has expired.'}, status=400)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']

        # Validate password strength
        user = reset_token.user
        try:
            validate_password(password, user=user)
        except DjangoValidationError as e:
            return Response({'error': e.messages}, status=400)

        user.set_password(password)
        user.save()
        reset_token.delete()

        return Response({'success': 'Password has been reset successfully.'}, status=200)
    
    
class RequestPasswordResetView(generics.GenericAPIView):
    serializer_class = api_serializers.RequestPasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try: 
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass

        response_message = {'message': 'If the email is registered, a reset link has been sent.'}

        # Send email password reset if user exists
        if 'user' in locals():
            token = api_models.PasswordResetToken.objects.create(user=user)
            # reset_link = f"{LOCAL_HOST}/reset-password/{token.token}/"
            reset_link = f"{LOCAL_HOST}/#/reset-password/{token.token}/"

            html_message = render_to_string('provider_auth/passwordresetemail.html', 
                                            {'reset_link': reset_link,
                                             'user': user,
                                             'year': datetime.now().year})
            # Send email with reset link
            send_mail(
                subject='Password Reset Request',
                message=f'Click the link to reset your password: {reset_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        return Response(response_message, status=200)



