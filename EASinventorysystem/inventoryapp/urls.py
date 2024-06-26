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
    path('account_logout/', views.account_logout, name='account_logout'),
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
    path('view_po_history/<int:pk>/', views.view_po_history, name='view_po_history'), 

    path('history_pro', views.history_PRO, name='history_pro'),
    path('view_pro_history/<int:pk>/', views.view_pro_history, name='view_pro_history'), 
    
    path('current_pros', views.requisition_order_list, name='current_pros'),
    path('view_po/<int:pk>/', views.view_po, name='view_po'), 

    path('update_PO_progress/<int:PO_pk>/', views.update_PO_progress, name='update_PO_progress'), 
    path('update_PRO_progress/<int:PRO_pk>/', views.update_PRO_progress, name='update_PRO_progress'), 
    
    path('close_po/<int:pk>/<int:account_id>/', views.close_po, name='close_po'),
    path('close_pro/<int:pk>/<int:account_id>/', views.close_pro, name='close_pro'),
    path('cancel_po/<int:pk>/<int:account_id>/', views.cancel_po, name='cancel_po'),
    path('cancel_pro/<int:pk>/<int:account_id>/', views.cancel_pro, name='cancel_pro'),
    path('cancel_po_specific/<int:pk>/<int:account_id>/', views.cancel_po_specific, name='cancel_po_specific'),
    path('cancel_pro_specific/<int:pk>/<int:account_id>/', views.cancel_pro_specific, name='cancel_pro_specific'),
    path('add_pro', views.add_requisition_order, name='add_pro'),
    path('view_pro/<int:pk>/', views.view_pro, name='view_pro'), 
    path('update_pro/<int:pk>/', views.update_pro, name='update_pro'),

    path('current_customers', views.customer_list, name='current_customers'),
    
    
    path('create_direct_customer', views.create_direct_customer, name='create_direct_customer'),
    path('create_consignee', views.create_consignee, name='create_consignee'),
    path('view_customer/<str:customer_type>/<int:customer_id>/', views.view_customer, name='view_customer'),
    path('update_direct_customer/<int:pk>/', views.update_direct_customer, name='update_direct_customer'),
    path('update_consignee/<int:pk>/', views.update_consignee, name='update_consignee'),

    path('categories_consignee_tags', views.categories_consignee_tags, name='categories_consignee_tags'),
    path('add_category', views.add_category, name='add_category'),
    path('view_category/<int:category_id>/', views.view_category, name='view_category'),

    path('generate_inventory_summary', views.generate_inventory_summary, name='generate_inventory_summary'),
    path('view_category_details/<int:category_id>/', views.view_category_details, name='view_category_details'),
    path('view_consignee_details/<int:consignee_id>/', views.view_consignee_tag_details, name='view_consignee_details'),
    path('create__consignee', views.create__consignee, name='create__consignee'),
    
    path('update_category/<int:pk>/', views.update_category, name='update_category'),
    path('update_tags/<int:pk>/', views.update_tags, name='update_tags'),

    path('my_account', views.my_account, name='my_account'),
    path('employee_accounts', views.employee_accounts, name='employee_accounts'),
    path('edit_my_account', views.edit_my_account, name='edit_my_account'),
    path('add_new_employee', views.add_new_employee, name='add_new_employee'),
    path('view_employee/<int:pk>/', views.view_employee, name='view_employee'),
    path('update_employee/<int:pk>/', views.update_employee, name='update_employee'),
    path('hide_account/<int:pk>/', views.hide_account, name='hide_account'),
    path('unhide_account/<int:pk>/', views.unhide_account, name='unhide_account'),


    path('generate_inventory_summary_screen', views.generate_inventory_summary_screen, name='generate_inventory_summary_screen'),

    path('edit_count', views.edit_count, name='edit_count'),
    path('inventory_update_history', views.inventory_update_history, name='inventory_update_history'),
    path('partially_fulfill/<int:pk>/', views.partially_fulfill, name='partially_fulfill'),
    path('history_partially_fulfilled/', views.history_partially_fulfilled, name='history_partially_fulfilled'),

    path('view_partially_fulfilled/<int:pk>/', views.view_partially_fulfilled, name='view_partially_fulfilled'),
    path('view_edit_count/<int:pk>/', views.view_edit_count, name='view_edit_count'),

    
]
