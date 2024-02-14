from django.contrib import admin
from .models import Account, Product, Category, Purchase_Order, Product_Requisition_Order, Count_Edit_History, Partially_Fulfilled_History
# Register your models here.

admin.site.register(Account)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Purchase_Order)
admin.site.register(Product_Requisition_Order)
admin.site.register(Count_Edit_History)
admin.site.register(Partially_Fulfilled_History)