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
    # path('add_po', views.add_purchase_order, name='add_po'),
    # path('add_po_second', views.add_po_second, name='add_po_second'), 
    path('add_po_direct_customer', views.add_purchase_order_direct_customer, name='add_po_direct_customer'),
    path('add_po_consignee', views.add_purchase_order_consignee, name='add_po_consignee'),

    path('update_po_direct_customer/<int:po_pk>/<int:c_pk>/', views.update_PO_direct_customer, name='update_po_direct_customer'),
    path('update_po_consignee/<int:po_pk>/<int:c_pk>/', views.update_PO_consignee, name='update_po_consignee'),
    
    path('history_po', views.history_PO, name='history_po'),
    
    path('current_pros', views.requisition_order_list, name='current_pros'),
    path('view_po/<int:pk>/', views.view_po, name='view_po'), 

    path('update_PO_progress/<int:PO_pk>/', views.update_PO_progress, name='update_PO_progress'), 
    path('update_PRO_progress/<int:PRO_pk>/', views.update_PRO_progress, name='update_PRO_progress'), 
    
    path('close_po/<int:pk>/<int:account_id>/', views.close_po, name='close_po'),
    path('close_pro/<int:pk>/<int:account_id>/', views.close_pro, name='close_pro'),
    path('add_pro', views.add_requisition_order, name='add_pro'),
    path('view_pro/<int:pk>/', views.view_pro, name='view_pro'), 
    path('update_pro/<int:pk>/', views.update_pro, name='update_pro'),

    path('current_customers', views.customer_list, name='current_customers'),
    
    
    path('create_direct_customer', views.create_direct_customer, name='create_direct_customer'),
    path('create_consignee', views.create_consignee, name='create_consignee'),
    path('view_customer/<str:customer_type>/<int:customer_id>/', views.view_customer, name='view_customer'),
    path('update_direct_customer/<int:pk>/', views.update_direct_customer, name='update_direct_customer'),
    path('update_consignee/<int:pk>/', views.update_consignee, name='update_consignee'),
]
