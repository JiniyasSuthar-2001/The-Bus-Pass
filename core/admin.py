from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Pass, Payment

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
    list_display = ['user', 'valid_until', 'is_valid_display', 'created_at']
    search_fields = ['user__username', 'barcode_data']
    list_filter = ['valid_until']
    
    def is_valid_display(self, obj):
        """
        Helper to display boolean icon for validity in Admin.
        """
        return obj.is_valid
    is_valid_display.boolean = True
    is_valid_display.short_description = 'Is Valid'

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Pass, PassAdmin)
admin.site.register(Payment)

admin.site.site_header = "Bus Pass Admin Dashboard"
admin.site.site_title = "Bus Pass Admin Portal"
admin.site.index_title = "Welcome to Bus Pass Admin"
