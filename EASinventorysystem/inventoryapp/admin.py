from django.contrib import admin
from .models import Account, Product, Category, Purchase_Order, Product_Ordered, Product_Requisition_Order, Stock_Ordered, Customer, Consignee, Consignee_Product, Count_Edit_History, Partially_Fulfilled_History
# Register your models here.

admin.site.register(Account)
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Purchase_Order)
admin.site.register(Product_Ordered)
admin.site.register(Product_Requisition_Order)
admin.site.register(Stock_Ordered)
admin.site.register(Customer)
admin.site.register(Consignee)
admin.site.register(Consignee_Product)
admin.site.register(Count_Edit_History)
admin.site.register(Partially_Fulfilled_History)