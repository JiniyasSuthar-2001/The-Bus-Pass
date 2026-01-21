from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Pass, Payment, City, Route, City, Route

class CustomUserAdmin(UserAdmin):
    """
    Customizing the User Admin Interface.
    Adds 'role' and 'balance' to list view and edit forms.
    """
    model = CustomUser
    list_display = ['username', 'email', 'role', 'balance', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'balance')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'balance')}),
    )
    search_fields = ['username', 'email']
    list_filter = ['role', 'is_staff', 'is_superuser']

class PassAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Pass model.
    Shows validity status in the list view.
    """
    list_display = ['user', 'is_active', 'created_at']
    search_fields = ['user__username', 'barcode_data']
    list_filter = ['is_active']

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Pass, PassAdmin)
admin.site.register(Payment)
admin.site.register(City)
admin.site.register(Route)

admin.site.site_header = "Bus Pass Admin Dashboard"
admin.site.site_title = "Bus Pass Admin Portal"
admin.site.index_title = "Welcome to Bus Pass Admin"
