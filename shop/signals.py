import requests
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order


@receiver(post_save, sender=Order)
def send_telegram_notification(sender, instance, created, **kwargs):
    if created:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        if token and chat_id:
            items = instance.items.all()
            product_details = ""

            for item in items:
                product_details += f"• {item.product.name} ({item.quantity} ta)\n"


            for item in items:
                product = item.product
                if product.stock <= product.min_stock_limit:
                    warning_text = (
                        f"⚠️ Diqqat! '{product.name}' tugayapti!\n"
                        f"📉 Qolgan soni: {product.stock} ta\n"
                        f"🔴 Minimal chegara: {product.min_stock_limit} ta\n"
                        f"‼️ Iltimos, omborni to'ldiring!"
                    )
                    requests.post(url, data={'chat_id': chat_id, 'text': warning_text})