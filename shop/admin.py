from django.contrib import admin

from .models import Category, Product, Order
from .models import Profile, User

from django.contrib.auth.admin import UserAdmin


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock'] # Admin panelni o'zida tahrirlash imkoniyati



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    list_editable = ['status']


admin.site.register(User)
admin.site.register(Profile)



# User modelini admin paneldan chiqarib, qayta (o'zimizga moslab) qo'shamiz
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Jadvalda ko'rinadigan ustunlar
    list_display = ('username', 'email', 'telegram_username', 'is_staff')

    # Ichiga kirganda tahrirlash qismi
    fieldsets = UserAdmin.fieldsets + (
        ('Telegram', {'fields': ('telegram_username',)}),
    )