# provider_auth/admin.py
from django.contrib import admin
from .models import User, Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 
        'full_name', 
        'role',  # ⬅️ Add role to list_display for an overview
        'npi_number',
        'is_verified', 
        'is_approved',
        'is_active', 
        'is_staff',
    )
    search_fields = ('email', 'full_name', 'npi_number')
    list_filter = ('is_verified', 'is_approved', 'is_staff', 'is_active', 'role') # ⬅️ Add role to list_filter

    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'npi_number')}),
        ('Permissions', {
            'fields': (
                'role', # ⬅️ Add role here so it is editable in the admin
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
    
admin.site.register(Profile)