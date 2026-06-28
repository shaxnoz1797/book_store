from django.urls import path
from .views import home_page, dashboard
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', home_page, name='home'),

    path('restock/<int:pk>/', views.restock_product, name='restock_product'),
    path('confirm-payment/<int:pk>/', views.confirm_payment, name='confirm_payment'),


    path('export-excel/', views.export_sales_excel, name='export_sales_excel'),
    path('invoice/pdf/<int:order_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    path('add-product/', views.add_product, name='add_product'),
    path('product/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('buy-book/<int:product_id>/', views.create_order, name='create_order'),


    path('todo/add/', views.add_todo, name='add_todo'),
    path('todo/delete/<int:pk>/', views.delete_todo, name='delete_todo'),
    path('toggle-todo/<int:pk>/', views.toggle_todo, name='toggle_todo'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/products/', views.dashboard_products, name='dashboard_products'),
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),
    path('dashboard/customers/', views.dashboard_customers, name='dashboard_customers'),
    path('dashboard/authors/', views.dashboard_authors, name='dashboard_authors'),
    path('dashboard/categories/', views.dashboard_categories, name='dashboard_categories'),

    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)