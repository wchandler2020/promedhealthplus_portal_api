# provider_auth/admin.py
from django.contrib import admin
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from .models import User, Profile, EmailVerificationToken

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 
        'full_name', 
        'role',
        'npi_number',
        'is_verified', 
        'is_approved',
        'is_active', 
        'is_staff',
    )
    search_fields = ('email', 'full_name', 'npi_number')
    list_filter = ('is_verified', 'is_approved', 'is_staff', 'is_active', 'role')

    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'npi_number')}),
        ('Permissions', {
            'fields': (
                'role',
                'is_active', 
                'is_approved', 
                'is_staff', 
                'is_superuser', 
                'groups', 
                'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        
        # Check if the password was changed
        if 'password' in form.changed_data:
            obj.set_password(obj.password)

        super().save_model(request, obj, form, change)
        
        # Send verification email for new, unverified users
        if is_new and not obj.is_verified:
            token, created = EmailVerificationToken.objects.get_or_create(user=obj)
            
            verification_link = f"https://wchandler2020.github.io/promedhealthplus_portal_client/#/verify-email/{token.token}"
            
            email_html_message = render_to_string('provider_auth/email_verification.html', {
                'user': obj,
                'verification_link': verification_link
            })

            send_mail(
                subject='Verify Your Email Address',
                message=f"Click the link to verify your email: {verification_link}",
                html_message=email_html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[obj.email],
                fail_silently=False
            )
            
admin.site.register(Profile)