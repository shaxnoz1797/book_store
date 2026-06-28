# 📚 Online Kitob Do'koni (Online Book Store)

Ushbu loyiha Python (Django freymvorki) yordamida yaratilgan to'liq onlayn do'kon tizimi hisoblanadi. Loyiha kitoblarni boshqarish, savatcha mantiqi va buyurtma berish jarayonlarini o'z ichiga oladi.

## ✨ Xususiyatlari (Features)

*   **Savatcha tizimi (Shopping Cart):** Foydalanuvchilar kitoblarni savatchaga qo'shishi, ularning sonini boshqarishi va umumiy summani hisoblashi mumkin.
*   **Buyurtma berish (Checkout):** Yetkazib berish manzili va telefon raqamini kiritish orqali buyurtma rasmiylashtirish.
*   **To'lov turlari:** Naqd pul va Plastik karta (Payme/Click simulyatsiyasi) orqali to'lov qilish imkoniyati.
*   **Telegram Integratsiya:** Har bir yangi buyurtma haqida administratorga Telegram Bot orqali darhol xabar boradi.
*   **PDF Invoys:** Har bir buyurtma uchun avtomatik tarzda PDF ko'rinishidagi invoys (chek) yaratish.
*   **Dashboard (Admin panel):** Do'kon egasi uchun mahsulotlar, buyurtmalar, mijozlar va mualliflarni boshqarish uchun maxsus interfeys.
*   **Stok boshqaruvi (Stock Management):** Har bir xariddan so'ng ombordagi kitoblar soni avtomatik kamayadi va mahsulot tugayotganda ogohlantirish beriladi.

## 🛠 Texnologiyalar (Tech Stack)

*   **Backend:** Python 3.11+, Django 5.x
*   **Frontend:** HTML5, CSS3, Bootstrap 5
*   **Database:** SQLite3 (Loyihani yurgizishga oson bo'lishi uchun)
*   **Kutubxonalar:** 
    *   `requests` (Telegram API uchun)
    *   `reportlab` (PDF yaratish uchun)
    *   `python-dotenv` (Maxfiy ma'lumotlarni saqlash uchun)

## 🚀 Loyihani ishga tushirish (Installation)

1. **Repozitoriyani klon qiling:**
   ```bash
   git clone https://github.com/shaxnoz1797/book_store.git
   cd bookstore
Virtual muhitni yarating va faollashtiring:

python -m venv .venv
# Windowsda:
.venv\Scripts\activate
Zaruriy kutubxonalarni yuklang:

pip install -r requirements.txt
Ma'lumotlar bazasini sozlang:

python manage.py makemigrations
python manage.py migrate
Admin (Superuser) yarating:

python manage.py createsuperuser
Loyihani ishga tushiring:

Bash
python manage.py runserver
🤖 Telegram Bot Sozlamalari
Loyihada Telegram xabarnomalar ishlashi uchun .env fayliga quyidagi ma'lumotlarni kiriting:

TELEGRAM_BOT_TOKEN=sizning_bot_tokeningiz
TELEGRAM_CHAT_ID=sizning_chat_idyingiz

👨‍💻 Muallif
Shaxnoz Axmedova- Python Junior Developer
