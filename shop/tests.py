from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Product, Category, Order, Author

User = get_user_model()



class BookStoreTest(TestCase):
    def setUp(self):
        """Test uchun boshlang'ich ma'lumotlarni tayyorlash"""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.staff_user = User.objects.create_superuser(username='admin', password='password123')

        self.category = Category.objects.create(name="Badiiy")
        self.author = Author.objects.create(name="O'tkir Hoshimov")
        self.product = Product.objects.create(
            category=self.category,
            author=self.author,
            name="Ikki eshik orasi",
            price=50000,
            stock=10,
            min_stock_limit=5,
            image="test_image.jpg"
        )



    def test_search_product(self):
        """1. Qidiruv tizimi ishlashini tekshirish"""

        response = self.client.get(reverse('home'), {'q': 'Ikki'})
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Ikki eshik orasi")



    def test_stock_reduction_after_order(self):
        """2. Buyurtma berilganda ombordagi kitob soni kamayishini tekshirish"""

        self.assertEqual(self.product.stock, 10)


        Order.objects.create(
            user=self.user,
            product=self.product,
            quantity=2
        )


        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)



    def test_dashboard_access(self):
        """3. Xavfsizlik: Dashboardga faqat admin kira olishini tekshirish"""

        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)

        # Admin kirmoqchi bo'lsa
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)



    def test_order_creation_view(self):
        """4. Buyurtma yaratish funksiyasi (View) ishlashini tekshirish"""
        self.client.login(username='testuser', password='password123')
        # create_order view-siga POST so'rovi yuboramiz
        url = reverse('create_order', args=[self.product.id])
        response = self.client.get(url)

        # Buyurtma yaratilganini tekshiramiz
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(response.status_code, 302)