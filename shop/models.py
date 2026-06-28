from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Rasm")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name



class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Kategoriya")
    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    description = models.TextField(verbose_name="Tavsif")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Narxi")
    stock = models.PositiveIntegerField(default=0, verbose_name="Ombordagi soni")
    min_stock_limit = models.PositiveIntegerField(default=5, verbose_name="minimal chegara")
    image = models.ImageField(upload_to='products/', verbose_name="Rasm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True)


    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('processing', 'Jarayonda'),
        ('completed', 'Yetkazib berildi'),
        ('cancelled', 'Bekor qilindi'),
    ]
    PAYMENT_METHODS = [
        ('cash', 'Naqd'),
        ('card', 'Plastik (Payme/Click)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Mijoz")
    # Bu yerda 'product' va 'quantity'ni o'chirib tashlaymiz, chunki ular OrderItem-ga o'tadi

    full_name = models.CharField(max_length=255, verbose_name="F.I.SH")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    address = models.TextField(verbose_name="Manzil/Lokatsiya")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cash',
                                      verbose_name="To'lov turi")

    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Umumiy narx", default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holat")
    is_paid = models.BooleanField(default=False, verbose_name="To'langanmi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sana")

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Sotilgan paytdagi narxi
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"



@receiver(post_save, sender=Order)
def update_stock_and_cache(sender, instance, created, **kwargs):
    if created:
        # keshni tozalash va xabar qoldiramiz
        cache.delete('low_stock_products')



class Cart(models.Model):
    # 2. User o'rniga settings.AUTH_USER_MODEL ni ishlatamiz
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}ning savatchasi"

    @property
    def total_price(self):
        items = self.items.all()
        total = sum([item.get_total_price for item in items])
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def get_total_price(self):
        return self.quantity * self.product.price


class Todo(models.Model):
    text = models.CharField(max_length=255, verbose_name="Eslatma matni")
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.text









