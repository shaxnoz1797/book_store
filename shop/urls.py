from django.urls import path
from .views import home_page, admin_dashboard

from . import views

urlpatterns = [
    path('', home_page, name='home'),
    path('dashboard/', admin_dashboard, name='dashboard'),

    path('restock/<int:pk>/', views.restock_product, name='restock_product'),
    path('confirm-payment/<int:pk>/', views.confirm_payment, name='confirm_payment'),

    # urls.py ichida
    path('export-excel/', views.export_sales_excel, name='export_sales_excel'),
    path('invoice/<int:order_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    path('add-product/', views.add_product, name='add_product'),
    path('product/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('buy-book/<int:product_id>/', views.create_order, name='create_order'),
    path('buy/<int:pk>/', views.product_buy, name='product_buy'),

    path('todo/add/', views.todo_add, name='todo_add'),
    path('todo/delete/<int:pk>/', views.todo_delete, name='todo_delete'),
    path('toggle-todo/<int:pk>/', views.toggle_todo, name='toggle_todo'),

]