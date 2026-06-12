import random
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib import messages
from django.db.models.functions import Coalesce
from django.db.models import Value
from django.views.decorators.http import require_POST
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.db.models import Count,DecimalField, IntegerField,F
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from .forms import ProductForm
from .models import Product, Category, Order, Mijoz, Todo

from .serializers import CategorySerializer, ProductSerializer,OrderSerializer

from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect
from datetime import  timezone

from django.utils import timezone  # Mana shu qator yetishmayapti
from datetime import timedelta     # Bu ham grafik uchun kerak
from django.db.models import Sum   # Bu savdo yig'indisini hisoblash uchun
from django.db.models import Q
import json
import openpyxl
from django.http import HttpResponse



def home_page(request):
    products = Product.objects.all().order_by('-created_at') # Hamma mahsulotlarni olish
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

User = get_user_model()


@staff_member_required
def admin_dashboard(request):

    todos = Todo.objects.all().order_by('-sana')
    # 1. Qidiruv so'zini olish
    query = request.GET.get('q', '').strip()

    # 2. Barcha buyurtmalar uchun asosiy so'rov (ORDERS_QUERYSET SHU YERDA YARATILADI)
    orders_queryset = Order.objects.all().select_related('user', 'product').order_by('-created_at')

    # 3. Filtrlash (Qidiruv bo'lsa hamma mos kelganini, bo'lmasa faqat 10 tasini ko'rsatish)
    if query:
        orders = orders_queryset.filter(
            Q(user__username__icontains=query) |
            Q(product__name__icontains=query)
        )
    else:
        orders = orders_queryset[:10]

    # --- GRAFIK UCHUN MA'LUMOTLAR ---
    today = timezone.now().date()
    days_list = []
    sales_list = []
    uzb_days = {'Monday': 'Dush', 'Tuesday': 'Sesh', 'Wednesday': 'Chor', 'Thursday': 'Pay', 'Friday': 'Jum',
                'Saturday': 'Shan', 'Sunday': 'Yak'}

    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        daily_sum = Order.objects.filter(
            created_at__date=target_date
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        days_list.append(uzb_days[target_date.strftime('%A')])
        sales_list.append(float(daily_sum))

    # --- STATISTIKALAR ---
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = Order.objects.aggregate(total=Count('user', distinct=True))['total'] or 0

    paid_revenue = Order.objects.filter(is_paid=True).aggregate(total=Sum('total_price'))['total'] or 0
    pending_revenue = Order.objects.filter(is_paid=False).aggregate(total=Sum('total_price'))['total'] or 0

    low_stock_products = Product.objects.filter(stock__lte=F('min_stock_limit'))

    # Eng ko'p sotilgan kitob
    top_product = Product.objects.annotate(
        total_sold=Coalesce(Sum('order__quantity'), Value(0))
    ).order_by('-total_sold').first()
    if top_product and top_product.total_sold == 0:
        top_product = None

    # --- YANGI QO'SHILGAN BO'LIMLAR (MIJOZLAR VA HISOBOTLAR) ---
    customers_list = User.objects.annotate(
        order_count=Count('order'),
        total_spent=Coalesce(Sum('order__total_price'), Value(0, output_field=DecimalField()))
    ).order_by('-total_spent')

    category_reports = Category.objects.annotate(
        total_sales=Coalesce(Sum('products__order__quantity'), Value(0, output_field=IntegerField())),
        total_revenue=Coalesce(Sum('products__order__total_price'), Value(0, output_field=DecimalField()))
    ).order_by('-total_sales')

    # Ombordagi hamma kitoblar
    all_products = Product.objects.all().order_by('-created_at')

    # --- AQLLI GAPLAR ---
    quotes = [
        "Yaxshi kitob — eng yaxshi do'st.",
        "Kitobsiz uy — derazasiz xonaga o'xshaydi.",
        "Bugungi kitobxon — ertangi rahbar.",
        "Mutolaa — aqlni charxlaydi.",
        "Kitoblar — vaqt dengizida suzib yuruvchi donolik kemalaridir.",
        "Podkast tavsiyasi: 'Navoiyxonlik' yoki 'Muvaffaqiyatli insonlar' turkumini eshiting."
    ]
    random_quote = random.choice(quotes)

    # Eng faol mijozni hisoblash
    eng_faol_data = Order.objects.values('user').annotate(
        jami=Count('user')
    ).order_by('-jami').first()

    eng_faol_mijoz = None
    if eng_faol_data:
        # Endi User tepada import qilingani uchun bu yerda xato bermaydi
        eng_faol_mijoz = User.objects.get(id=eng_faol_data['user'])

    # Masalan, agar sizda janrlar queryseti bo'lsa:
    janr_nomlari = ["Dramma", "Badiiy", "Detektiv"]  # Buni bazadan olingan nomlar bilan almashtiring
    sotilgan_soni = [16, 7, 6]  # Buni bazadan olingan raqamlar bilan almashtiring

    top_mijozlar = User.objects.select_related('profile').annotate(
        b_soni=Count('order'),
        jami_sarf=Sum('order__total_price')
    ).order_by('-b_soni')[:5]

    # Haftalik savdo dinamikasi (Oxirgi 7 kun)
    bugun = timezone.now().date()
    hafta_kunlari = []
    savdo_miqdori = []

    for i in range(6, -1, -1):
        kun = bugun - timedelta(days=i)
        jami = Order.objects.filter(created_at__date=kun).aggregate(Sum('total_price'))['total_price__sum'] or 0
        hafta_kunlari.append(kun.strftime('%d-%b'))  # Masalan: 11-Jun
        savdo_miqdori.append(float(jami))

    context = {
            'quote': random_quote,
            'orders': orders,
            'query': query,
            'days': json.dumps(days_list),
            'sales_data': json.dumps(sales_list),
            'total_products': total_products,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'paid_revenue': paid_revenue,
            'pending_revenue': pending_revenue,
            'low_stock_products': low_stock_products,
            'top_product': top_product,
            'all_products': all_products,
            'customers_list': customers_list,
            'category_reports': category_reports,
            'eng_faol_mijoz': eng_faol_mijoz,
            'janr_nomlari': janr_nomlari,
            'sotilgan_soni': sotilgan_soni,
            'top_mijozlar': top_mijozlar,
            'todos': todos,
            'hafta_kunlari': hafta_kunlari,
            'savdo_miqdori': savdo_miqdori,

    }

    return render(request, 'dashboard.html', context)



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price'] # Kategoriya va narx bo'yicha filter
    search_fields = ['name', 'description'] # Ismi bo'yicha qidirish
    ordering_fields = ['price', 'created_at'] # Narx va sana bo'yicha saralash



class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # shop/views.py ichida
    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        total_price = product.price * quantity
        # Faqat saqlaymiz, qolganini Signal hal qiladi
        serializer.save(user=self.request.user, total_price=total_price)



def restock_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # 1. Ombordagi soniga 10 ta qo'shamiz
    product.stock += 10
    product.save()

    # 2. Redis keshini o'chiramiz (chunki endi bu mahsulot "kam qolganlar" ro'yxatidan chiqishi kerak)
    cache.delete('low_stock_products')

    # 3. Yana dashboardga qaytaramiz
    return redirect('dashboard')  # Dashboard URL nomini tekshiring


def confirm_payment(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.is_paid = True
    order.status = 'completed'  # To'langach holatini ham o'zgartiramiz
    order.save()

    # Umumiy tushum o'zgargani uchun keshni tozalasak ham bo'ladi (ixtiyoriy)
    cache.delete('total_revenue_cache')

    return redirect('dashboard')



def export_orders_excel(request):
    # 1. Yangi Excel kitobi yaratamiz
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Buyurtmalar"

    # 2. Jadval ustunlari (Header)
    columns = ['ID', 'Mijoz', 'Mahsulot', 'Narxi', 'Holati', 'Sana']
    sheet.append(columns)

    # 3. Bazadan ma'lumotlarni olib, Excelga qo'shamiz
    orders = Order.objects.all().order_by('-created_at')

    for order in orders:
        sheet.append([
            order.id,
            order.user.username,
            str(order.product) if order.product else "Noma'lum",
            order.total_price,
            order.get_status_display(),  # 'completed' emas, 'Yetkazib berildi' deb chiqishi uchun
            order.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    # 4. Faylni brauzerga yuboramiz
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=buyurtmalar.xlsx'

    workbook.save(response)
    return response


def generate_invoice_pdf(request, order_id):
    # 1. Buyurtmani bazadan olamiz
    order = Order.objects.get(id=order_id)

    # 2. PDF javobini tayyorlaymiz
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoys_{order.id}.pdf"'

    # 3. PDF "polotno"sini yaratamiz
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # --- PDF DIZAYNI ---
    # Sarlavha
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width / 2, height - 50, "KITOB DO'KONI - INVOYS")

    p.setFont("Helvetica", 12)
    p.line(50, height - 70, width - 50, height - 70)  # Chiziq tortish

    # Ma'lumotlar
    p.drawString(50, height - 100, f"Buyurtma ID: #{order.id}")
    p.drawString(50, height - 120, f"Sana: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(50, height - 140, f"Mijoz: {order.user.username}")

    # Jadval sarlavhasi
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 180, "Mahsulot")
    p.drawString(300, height - 180, "Soni")
    p.drawString(400, height - 180, "Narxi")
    p.drawString(500, height - 180, "Jami")

    p.line(50, height - 185, width - 50, height - 185)

    # Jadval mazmuni
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 210, f"{order.product.name}")
    p.drawString(300, height - 210, f"{order.quantity} ta")
    p.drawString(400, height - 210, f"{order.product.price} so'm")
    p.drawString(500, height - 210, f"{order.total_price} so'm")

    p.line(50, height - 230, width - 50, height - 230)

    # Yakuniy summa
    p.setFont("Helvetica-Bold", 14)
    p.drawString(400, height - 260, f"TO'LOV: {order.total_price} so'm")

    # Pastki qism
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2, 50, "Xaridingiz uchun rahmat!")

    # PDF-ni yopamiz
    p.showPage()
    p.save()

    return response


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Saqlab bo'lgach dashboardga qaytadi
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form, 'quote': "Yangi bilimlar manbai — yangi kitoblarda!"})


def create_order(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')  # Avval login qilish shart

    product = get_object_or_404(Product, id=product_id)
    if product.stock > 0:
        # Yangi buyurtma yaratamiz
        Order.objects.create(
            user=request.user,
            product=product,
            quantity=1,
            is_paid=False  # Hali to'lanmagan
        )
        # Eslatma: Modelda yozgan save metodimiz narxni va stockni o'zi hal qiladi
        return redirect('dashboard')  # Buyurtma tushganini ko'rish uchun dashboardga o'tamiz
    return redirect('home')


# Tahrirlash funksiyasi
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'add_product.html', {'form': form, 'edit_mode': True, 'product': product})

# O'chirish funksiyasi
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('dashboard')


# views.py ichida
def product_buy(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.stock > 0:
        Order.objects.create(
            user=request.user,
            product=product,
            quantity=1
        )
    return redirect('admin_dashboard') # 'dashboard.html' emas, url nomini yozing


# views.py ichida




# 1. Qo'shish funksiyasi (Sizda nomi 'todo_add' yoki shunga o'xshash bo'lishi mumkin)
def todo_add(request):
    if request.method == 'POST':
        matn_input = request.POST.get('todo_matni')  # HTMLdagi 'name' bilan bir xil bo'lishi kerak

        if matn_input:  # Agar input bo'sh bo'lmasa
            yangi_todo = Todo(matn=matn_input)
            yangi_todo.save()  # BAZAGA SAQLASH
            messages.success(request, "Yangi eslatma muvaffaqiyatli qo'shildi! ➕")
        else:
            messages.error(request, "Matn kiriting!")

    return redirect('dashboard')

# 2. O'chirish funksiyasi
def todo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.delete()
    # O'chirilganda xato (qizil) xabarini beramiz
    messages.error(request, "Eslatma o'chirib tashlandi! 🗑️")
    return redirect('dashboard')

# 3. Checkbox (toggle) funksiyasida xabar QOLMAYDI
def toggle_todo(request, pk):
    todo_obj = get_object_or_404(Todo, pk=pk)
    # is_completed maydonini o'zgartiramiz
    todo_obj.is_completed = not todo_obj.is_completed
    todo_obj.save()
    return redirect('dashboard')
