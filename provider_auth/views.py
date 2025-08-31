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
from django.conf import settings
from decimal import Decimal
from twilio.rest import Client
from django.core.mail import send_mail
from dotenv import load_dotenv
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO
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

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime

from provider_auth import serializers as api_serializers


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
            
class CreateOrderView(generics.CreateAPIView):
    serializer_class = api_serializers.OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        request.data['provider'] = request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        order = serializer.instance
        self.send_invoice_email(order)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def send_invoice_email(self, order):
        sales_rep_email = order.provider.profile.sales_rep.email
        recipient_list = [
            order.provider.email,
            sales_rep_email,
            settings.DEFAULT_FROM_EMAIL
        ]

        subject = f"Invoice for Order #{order.id}"

        # Render HTML
        html_content = render_to_string('email/order_invoice.html', {'order': order})

        # Generate PDF
        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)
        pdf_file.seek(0)

        # Email with attachment
        email = EmailMessage(
            subject=subject,
            body="Please find attached the invoice for your recent order.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach(f"invoice_order_{order.id}.pdf", pdf_file.read(), 'application/pdf')
        email.send(fail_silently=False)


