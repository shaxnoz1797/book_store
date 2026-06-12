import requests
import environ
env = environ.Env()
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    if created:
        token = env('TELEGRAM_BOT_TOKEN')
        chat_id = env('TELEGRAM_CHAT_ID')
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        # 1. Buyurtma xabari
        message = (
            f"🛍 Yangi buyurtma!\n\n"
            f"🆔 Buyurtma ID: {instance.id}\n"
            f"👤 Mijoz: {instance.user.username}\n"
            f"📦 Mahsulot: {instance.product.name}\n"
            f"🔢 Soni: {instance.quantity} ta\n"
            f"💰 Jami: {instance.total_price} so'm\n"
            f"📅 Sana: {instance.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        requests.post(url, data={'chat_id': chat_id, 'text': message})

        # 2. Kam qolgan bo'lsa ogohlantirish (faqat tekshiramiz, ayirmaymiz)
        product = instance.product
        if product.stock <= product.min_stock_limit:
            warning_text = (
                f"⚠️ Diqqat! '{product.name}' mahsuloti tugayapti!\n\n"
                f"📉 Omborda qolgan soni: {product.stock} ta\n"
                f"🔴 Minimal chegara: {product.min_stock_limit} ta\n"
                f"‼️ Iltimos, omborni to'ldiring!"
            )
            requests.post(url, data={'chat_id': chat_id, 'text': warning_text})