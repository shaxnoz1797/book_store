from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile



@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Telegram', {'fields': ('telegram_username',)}),
    )


admin.site.register(Profile)