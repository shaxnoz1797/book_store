from django.contrib import admin
from .models import Category, Product, Order, Author, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock']



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity']  # Adminlar buni o'zgartira olmasin (faqat ko'rsin)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # 'product' va 'quantity'ni list_display dan olib tashladik
    list_display = ['id', 'user', 'full_name', 'total_price', 'status', 'is_paid', 'created_at']
    list_filter = ['status', 'is_paid', 'created_at']
    search_fields = ['full_name', 'phone', 'address']

    # Buyurtma ichiga kirganda mahsulotlar ro'yxatini chiqaradi
    inlines = [OrderItemInline]


admin.site.register(Author)