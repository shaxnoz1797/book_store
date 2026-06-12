from django.test import TestCase
from .models import Category, Product

class ProductModelTest(TestCase):
    def setUp(self):
        # Test uchun vaqtinchalik ma'lumot yaratamiz
        self.category = Category.objects.create(name="Test Kitoblar")
        self.product = Product.objects.create(
            category=self.category,
            name="Django Qo'llanma",
            price=50000,
            stock=10
        )

    def test_product_creation(self):
        # Mahsulot to'g'ri yaratilganini tekshiramiz
        self.assertEqual(self.product.name, "Django Qo'llanma")
        self.assertEqual(self.product.stock, 10)