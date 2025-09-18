from django.contrib import admin
from .models import User, Profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class ProfileInLine(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInLine,)
    list_display = (
        'email', 
        'full_name', 
        'npi_number',
        'is_verified', 
        'is_approved',
        'is_active', 
        'is_staff',
    )
    search_fields = ('email', 'full_name', 'npi_number')
    list_filter = ('is_verified', 'is_approved', 'is_staff', 'is_active')

    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'npi_number')}),
        ('Permissions', {
            'fields': (
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

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

