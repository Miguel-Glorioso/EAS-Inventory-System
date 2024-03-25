"""
URL configuration for EASinventorysystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.account_login, name='account_login'),
    path('current_inventory', views.inventory_list, name='current_inventory'),
    path('add_product', views.add_product, name='add_product'),
    path('view_product/<int:product_pk>/', views.view_product, name='view_product'),
    path('update_product/<int:pk>/', views.update_product, name='update_product'),
    path('current_pos', views.purchase_order_list, name='current_pos'),
    path('add_po', views.add_purchase_order, name='add_po'),
    path('view_po/<int:pk>/', views.view_po, name='view_po'), 
    path('close_po/<int:pk>/', views.close_po, name='close_po'),
    path('current_customer', views.customer_list, name='customer_list'),
    path('current_pros', views.requisition_order_list, name='current_pros'),
    path('add_pro', views.add_requisition_order, name='add_pro'),
    path('view_pro/<int:pk>/', views.view_pro, name='view_pro'), 
    path('create_direct_customer', views.create_direct_customer, name='create_direct_customer'),
    path('create_consignee', views.create_consignee, name='create_consignee'),
]
