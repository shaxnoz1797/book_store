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
            # 1. Buyurtma ichidagi barcha mahsulotlarni yig'ish
            # Eslatma: Agar signals.py mahsulotlarni ko'rmasa, quyidagi qismga e'tibor bering
            items = instance.items.all()
            product_details = ""

            for item in items:
                product_details += f"• {item.product.name} ({item.quantity} ta)\n"

            # 2. Xabar matnini shakllantirish
            # message = (
            #     f"Yangi buyurtma! ✅\n"
            #     f"ID: #{instance.id}\n"
            #     f"Mijoz: {instance.full_name}\n"
            #     f"Telefon: {instance.phone}\n"
            #     f"Manzil: {instance.address}\n"
            #     f"To'lov: {instance.get_payment_method_display()}\n\n"
            #     f"Mahsulotlar:\n{product_details if product_details else 'Savatcha tahlil qilinmoqda...'}\n"
            #     f"Jami summa: {instance.total_price} so'm"
            # )

            # try:
            #     requests.post(url, data={'chat_id': chat_id, 'text': message})
            # except Exception as e:
            #     print(f"Telegram yuborishda xato: {e}")

            # 3. Omborda kam qolgan mahsulotlarni tekshirish
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