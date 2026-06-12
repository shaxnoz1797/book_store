from django.contrib.auth.models import User, AbstractUser
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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Mijoz")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Mahsulot")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Soni")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Umumiy narx", editable=False,
                                      blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holat")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sana")
    is_paid = models.BooleanField(default=False, verbose_name="To'langanmi?")  # Yangi maydon

    def save(self, *args, **kwargs):
        # 1. Narxni avtomatik hisoblash (mahsulot narxi * soni)
        if self.product:
            self.total_price = self.product.price * self.quantity

        # 2. Ombordagi sonini kamaytirish (faqat yangi buyurtma ochilganda)
        if not self.pk:  # Agar bu yangi buyurtma bo'lsa (ID si hali yo'q bo'lsa)
            self.product.stock -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"


@receiver(post_save, sender=Order)
def update_stock_and_cache(sender, instance, created, **kwargs):
    if created:
        # BU YERDAN ayirish kodini o'chirib tashladik!
        # Faqat keshni tozalash va xabar qoldiramiz
        cache.delete('low_stock_products')
        print(f"DEBUG: Buyurtma yaratildi, xabar yuborilmoqda...")


class Mijoz(models.Model):  # Mana shu qavs ichidagi qism bo'lishi kerak
    ism_familiya = models.CharField(max_length=200)



class Todo(models.Model):
    matn = models.CharField(max_length=255, verbose_name="Eslatma matni")
    bajarildi = models.BooleanField(default=False)
    sana = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.matn



class Profile(models.Model):
    # 'User' so'zi o'rniga 'settings.AUTH_USER_MODEL' ishlatamiz
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    telegram_username = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} profili"





