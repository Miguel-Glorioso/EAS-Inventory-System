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
    path('current_purchase_orders', views.purchase_order_list, name='current_purchase_orders'),
    path('add_purchase_order', views.add_purchase_order, name='add_purchase_order'),
    path('view_po', views.view_po, name='view_po'), #TIMMY ADDED
]
