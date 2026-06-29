import os
import random
import json
import openpyxl
from datetime import timedelta

import requests
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F, Q, DecimalField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

# DRF va boshqalar
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import Product, Category, Order, Todo, Author, Cart, CartItem, OrderItem
from .forms import ProductForm
from .serializers import CategorySerializer, ProductSerializer, OrderSerializer




User = get_user_model()



def home_page(request):
    # 1. Barcha mahsulotlarni olish
    products_list = Product.objects.all().order_by('-created_at')

    # Qidiruv (Search)
    query = request.GET.get('q')
    if query:
        products_list = products_list.filter(
            Q(name__icontains=query) |
            Q(author__name__icontains=query)  # author__ ichidagi name maydonini ko'rsatdik
        )

    # 3. Kategoriya bo'yicha filter (Janrlar uchun)
    cat_id = request.GET.get('category')
    if cat_id:
        products_list = products_list.filter(category_id=cat_id)

    # 4. Pagination (Sahifalash) - Har sahifada 12 ta mahsulot
    paginator = Paginator(products_list, 3)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': cat_id,
    }
    return render(request, 'home.html', context)



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer




@staff_member_required
def dashboard(request):
    # 1. Statik raqamlar
    products_count = Product.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('total_price'))['total'] or 0
    orders_count = Order.objects.count()
    customers_count = User.objects.count()

    # 2. Grafiklar ma'lumotlari
    genre_data = Category.objects.annotate(count=Count('products'))
    genre_labels = [c.name for c in genre_data]
    genre_counts = [c.count for c in genre_data]

    last_orders = Order.objects.order_by('-created_at')[:7]
    sales_labels = [o.created_at.strftime('%d-%m') for o in last_orders][::-1]
    sales_amounts = [float(o.total_price) for o in last_orders][::-1]

    # 3. Top Mijozlar
    top_mijozlar = User.objects.annotate(
        b_soni=Count('order'),
        jami_sarf=Sum('order__total_price')
    ).filter(b_soni__gt=0).order_by('-jami_sarf')[:5]

    # 4. Eslatmalar
    todos = Todo.objects.all().order_by('-id')
    low_stock_products = Product.objects.filter(stock__lt=F('min_stock_limit'))

    # Hikmatlar
    quote = cache.get('daily_quote')

    if not quote:
        hikmatlar = [
            "Bilim - bu dunyodagi eng kuchli qurol.",
            "Bugungi kitobxon ertangi rahbar.",
            "Kitob - eng yaqin do'st.",
            "Muvaffaqiyat kaliti - bilimda.",
            "Kitob — sukutdagi ustoz, bilim esa umrboqiy boylikdir.",
            "Bir sahifa kitob o‘qish, yuzta bekor suhbatdan foydaliroq.",
            "Bilimga sarflangan vaqt hech qachon zoye ketmaydi.",
            "Kitob o‘qigan inson ming hayot yashaydi, o‘qimagan esa faqat bitta.",
            "Bilim — insonni yuksaltiradigan eng qudratli kuch.",
            "Kutubxona — kelajak sari ochilgan eshikdir.",
            "Kitoblar qalbni tarbiyalaydi, bilim esa aqlni charxlaydi.",
            "Bugun o‘qilgan bir kitob, ertangi muvaffaqiyatning poydevoridir.",
            "Bilim izlagan yo‘lini topadi, dangasa esa bahona topadi.",
            "Eng katta sarmoya — o‘z ustingda ishlash va bilim olishdir."
        ]
        quote = random.choice(hikmatlar)
        # 86400 sekund = 24 soatga saqlab qo'yamiz
        cache.set('daily_quote', quote, 86400)

    context = {
        'products_count': products_count,
        'total_revenue': total_revenue,
        'orders_count': orders_count,
        'customers_count': customers_count,
        'genre_labels': genre_labels,
        'genre_counts': genre_counts,
        'sales_labels': sales_labels,
        'sales_amounts': sales_amounts,
        'top_mijozlar': top_mijozlar,
        'todos': todos,
        'low_stock_products': low_stock_products,
        'quote': quote,
}

    context['quote'] = quote
    return render(request, 'dashboard.html', context)



class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']



class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        total_price = product.price * quantity

        serializer.save(user=self.request.user, total_price=total_price)



@staff_member_required
@require_POST
def restock_product(request, pk): #omborni toldirish
    product = get_object_or_404(Product, pk=pk)

    # 1. Ombordagi soniga 10 ta qo'shamiz
    product.stock += 10
    product.save()

    # 2. Redis keshini o'chiramiz
    cache.delete('low_stock_products')

    # 3. Yana dashboardga qaytaramiz
    return redirect('dashboard')


@staff_member_required
@require_POST
def confirm_payment(request, pk):   #(to'lovni tasdiqlash)
    order = get_object_or_404(Order, pk=pk)
    order.is_paid = True
    order.status = 'completed'
    order.save()
    return redirect('dashboard')



@staff_member_required
def export_sales_excel(request):  #(hisobot olish)
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Haftalik Savdo"

        # Sarlavhalar
        ws.append(['Sana', 'Savdo miqdori (so\'m)'])

        today = timezone.now().date()
        # Oxirgi 7 kunni Excelga yozish
        for i in range(6, -1, -1):
            kun = today - timedelta(days=i)

            jami = Order.objects.filter(created_at__date=kun).aggregate(Sum('total_price'))['total_price__sum'] or 0
            ws.append([kun.strftime('%Y-%m-%d'), float(jami)])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=haftalik_savdo.xlsx'
        wb.save(response)
        return response
    except Exception as e:
        return HttpResponse(f"Xatolik yuz berdi: {e}")


def generate_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # PDF yaratish sozlamalari...
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Sarlavha va Mijoz ma'lumotlari
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, f"Invoys #{order.id}")

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Mijoz: {order.full_name}")
    p.drawString(100, height - 100, f"Telefon: {order.phone}")
    p.drawString(100, height - 120, f"Sana: {order.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Jadval sarlavhasi
    p.line(100, height - 140, 500, height - 140)
    p.drawString(100, height - 160, "Kitob nomi")
    p.drawString(350, height - 160, "Soni")
    p.drawString(430, height - 160, "Narxi")
    p.line(100, height - 170, 500, height - 170)

    # MANA BU YERDA LOOP (SIKL) ISHLATAMIZ
    y_position = height - 190

    for item in order.items.all():
        # Kitob nomini chiqaramiz
        p.drawString(100, y_position, f"{item.product.name}")
        # Sonini chiqaramiz
        p.drawString(350, y_position, f"{item.quantity} ta")
        # Narxini chiqaramiz
        p.drawString(430, y_position, f"{item.price} so'm")

        y_position -= 20


        if y_position < 100:
            p.showPage()
            y_position = height - 50

    # Umumiy summa
    p.line(100, y_position - 10, 500, y_position - 10)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y_position - 30, f"Jami to'lov: {order.total_price} so'm")

    p.showPage()
    p.save()
    return response


@staff_member_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():

            form.save()
            messages.success(request, "Kitob muvaffaqiyatli qo'shildi! ✅")
            return redirect('dashboard')
        else:

            messages.error(request, "Formada xatolik bor, iltimos ma'lumotlarni tekshiring! ❌")
    else:
        form = ProductForm()

    return render(request, 'add_product.html', {'form': form})



def create_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('checkout')




@staff_member_required
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


@staff_member_required
@require_POST
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Mahsulot muvaffaqiyatli o'chirildi.")
    return redirect('dashboard')



@staff_member_required
def add_todo(request):
    if request.method == 'POST':
        # 1. Formadan kelgan matnni olamiz
        todo_text = request.POST.get('todo_matni')

        if todo_text:  # Agar matn bo'sh bo'lmasa
            # 2. O'sha olingan matnni (todo_text) bazadagi 'text' maydoniga saqlaymiz
            Todo.objects.create(text=todo_text)

            messages.success(request, "Yangi eslatma muvaffaqiyatli qo'shildi! ➕")
        else:
            messages.error(request, "Matn kiriting!")

    return redirect('dashboard')


@staff_member_required
def delete_todo(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    todo.delete()
    # O'chirilganda xato (qizil) xabarini beramiz
    messages.error(request, "Eslatma o'chirib tashlandi! 🗑️")
    return redirect('dashboard')




@staff_member_required
def toggle_todo(request, pk):
    todo_obj = get_object_or_404(Todo, pk=pk)
    # is_completed maydonini o'zgartiramiz
    todo_obj.is_completed = not todo_obj.is_completed
    todo_obj.save()
    return redirect('dashboard')


@staff_member_required
def dashboard_products(request):
    query = request.GET.get('q', '').strip()
    # Faqat mahsulotlarni olamiz
    products = Product.objects.all().order_by('-id')

    if query:
        products = products.filter(name__icontains=query)

    context = {
        'all_products': products,
        'query': query,
    }
    return render(request, 'dashboard_products.html', context)


@staff_member_required
def dashboard_orders(request):

    orders = Order.objects.select_related('user').prefetch_related('items__product').all().order_by('-created_at')

    return render(request, 'dashboard_orders.html', {'orders': orders})


@staff_member_required
def dashboard_customers(request):
    # Mijozlarni xaridlari bo'yicha hisoblab chiqish
    customers = User.objects.annotate(
        order_count=Count('order'),
        total_spent=Coalesce(Sum('order__total_price'), Value(0, output_field=DecimalField()))
    ).order_by('-total_spent')

    return render(request, 'dashboard_customers.html', {'customers': customers})


@staff_member_required
def dashboard_authors(request):
    authors = Author.objects.all().order_by('name')
    return render(request, 'dashboard_authors.html', {'authors': authors})



@staff_member_required
def dashboard_categories(request):
    categories = Category.objects.all()
    return render(request, 'dashboard_categories.html', {'categories': categories})



@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('home')



@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart_detail.html', {'cart': cart})



@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)


    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')

        # 1. Buyurtmani yaratamiz
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            payment_method=payment_method,
            total_price=cart.total_price
        )

        # 2. Kitoblarni ulaymiz (for loop)
        product_details = ""
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            product_details += f"• {item.product.name} ({item.quantity} ta)\n"

            # Stokni kamaytirish
            item.product.stock -= item.quantity
            item.product.save()

        # 3. !!! TELEGRAMGA XABAR YUBORISH (Endi hamma kitoblar tayyor) !!!
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if token and chat_id:
            message = (
                f"Yangi buyurtma! ✅\n"
                f"ID: #{order.id}\n"
                f"Mijoz: {order.full_name}\n"
                f"Telefon: {order.phone}\n"
                f"Manzil: {order.address}\n\n"
                f"Mahsulotlar:\n{product_details}\n"
                f"Jami summa: {order.total_price} so'm"
            )
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            try:
                requests.post(url, data={'chat_id': chat_id, 'text': message})
            except:
                pass

        # 4. Savatchani tozalaymiz
        cart.items.all().delete()

        return render(request, 'order_success.html', {'order': order})

    return render(request, 'checkout.html', {'cart': cart})



def book_detail(request, pk):
    book = get_object_or_404(Product, pk=pk)
    return render(request, 'book_detail.html', {'book': book})