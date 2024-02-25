from django.shortcuts import render, redirect, get_object_or_404
from . models import Product, Category, Account,Consignee, Consignee_Product, Purchase_Order, Products_Ordered
from django.http import HttpResponseRedirect
from django.core.files.storage import default_storage
from django.core.files import File


# Create your views here.

def account_login(request):
    if request.method == 'POST':
        login_username = request.POST.get('user_name')
        login_password = request.POST.get('password')

        try:
            account = Account.objects.get(Username=login_username)

            if account.getPassword() == login_password:
                global  id 
                                
                id = account.pk
                return redirect('current_inventory')
            else:
                error_msg = "Invalid Username/Password"
                return render(request, 'inventoryapp/login.html', {'error_msg': error_msg})
            
        except:        
            error_msg = "Invalid Username/Password"
            return render(request, 'inventoryapp/login.html', {'error_msg': error_msg})

    else:
        return render(request, 'inventoryapp/login.html')


def inventory_list(request):
    all_inventory = Product.objects.all()
    all_consignee_products = Consignee_Product.objects.all()
    return render(request, 'inventoryapp/current_inventory.html', {'products':all_inventory, 'consignee_products':all_consignee_products})


def add_product(request):
    categories = Category.objects.all()
    consignees = Consignee.objects.all()
    if request.method == 'POST':
        Product_Name = request.POST.get('product_name')
        Product_Price = request.POST.get('product_price')
        EAS_Product_ID = request.POST.get('eas_id')
        Product_SKU = request.POST.get('product_sku')
        Product_Initial_Count = request.POST.get('product_initial_count')
        Product_Picture = request.FILES.get('product_picture') 
        Product_Stock_threshold = request.POST.get("product_stock_level_threshold")
        Product_Category = request.POST.get('product_category')
        Product_Consignees = request.POST.getlist('product_consignees')

        if Product_Stock_threshold == 0:
              Product_Stock_threshold = None
        

        product = Product.objects.create(
            EAS_Product_ID = EAS_Product_ID,
            Name = Product_Name,
            Picture = Product_Picture,
            SKU = Product_SKU,
            Price = Product_Price,
            Actual_Inventory_Count = Product_Initial_Count,
            Reserved_Inventory_Count = 0,
            To_Be_Received_Inventory_Count = 0,
            Visibility = True,
            Product_Low_Stock_Threshold = Product_Stock_threshold, 
            Category = Category.objects.get(pk=Product_Category)
        )

        if Product_Consignees:
            product = Product.objects.get(EAS_Product_ID=EAS_Product_ID)

        
        for consignee_id in Product_Consignees:
            consignee = Consignee.objects.get(pk=consignee_id)
            Consignee_Product.objects.create(
                Product_ID=product,
                Consignee_ID=consignee
            )
        return redirect('current_inventory')
    else:
        return render(request, 'inventoryapp/add_product.html',  {'categories': categories, 'consignees': consignees})


def view_product(request, pk):
    p = get_object_or_404(Product, pk=pk)
    con_p = Consignee_Product.objects.filter(Product_ID=pk)
    return render(request, 'inventoryapp/view_product.html', {'p':p, 'con_p':con_p })

def update_product(request, pk):
    p = get_object_or_404(Product, pk=pk)
    con_p = Consignee_Product.objects.filter(Product_ID=pk)
    con_p_ids = con_p.values_list('Consignee_ID', flat=True)
    categories = Category.objects.all()
    consignees = Consignee.objects.all()
    if request.method == 'POST':
        Product_Name = request.POST.get('product_name')
        Product_Price = request.POST.get('product_price')
        EAS_Product_ID = request.POST.get('eas_id')
        Product_SKU = request.POST.get('product_sku')
        Product_Picture = request.FILES.get('product_picture')
        Image_removed = request.POST.get('removed_product_picture')
        Product_Category = request.POST.get('product_category')
        Product_Stock_threshold = request.POST.get("product_stock_level_threshold")
        Product_Visibility = request.POST.get('product_visibility')
        Product_Consignees = request.POST.getlist('product_consignees')
        if Product_Stock_threshold == 0:
              Product_Stock_threshold = None

        product = Product.objects.get(pk=pk)
        if Image_removed == 'removed':
            previous_picture_filename = product.Picture.name
            product.Picture = None
            product.save()
            
            if previous_picture_filename:
                default_storage.delete(previous_picture_filename)
        
        elif Product_Picture is not None:
            previous_picture_filename = product.Picture.name
            product.Picture = Product_Picture
            product.save()
            
            if previous_picture_filename:
                default_storage.delete(previous_picture_filename)
        
        Product.objects.filter(pk=pk).update(
            EAS_Product_ID=EAS_Product_ID,
            Name=Product_Name,
            SKU=Product_SKU,
            Price=Product_Price,
            Visibility=Product_Visibility,
            Product_Low_Stock_Threshold=Product_Stock_threshold,
            Category= Product_Category
        )

        for consignee_id in Product_Consignees:
            consignee = Consignee.objects.get(pk=consignee_id)
            if not con_p.filter(Consignee_ID=consignee).exists():
                Consignee_Product.objects.create(
                    Product_ID=product,
                    Consignee_ID=consignee
                )
        
        for con_ids in con_p_ids:
            if str(con_ids) not in Product_Consignees:
                Consignee_Product.objects.filter(Consignee_ID=con_ids, Product_ID=pk).delete()
        
        
        return redirect('view_product', pk=pk)
    else:
        return render(request, 'inventoryapp/update_product.html', {'p':p, 'con_p':con_p, 'con_p_ids':con_p_ids, 'categories': categories,  'consignees': consignees})
    
def purchase_order_list(request):
    all_purchase_orders = Purchase_Order.objects.all()
    print(all_purchase_orders)
    return render(request, 'inventoryapp/current_purchase_orders.html', {'purchase_orders':all_purchase_orders})

def add_purchase_order(request):
    if request.method == 'POST':
        print("yes")
    else:
        return render(request, 'inventoryapp/add_purchase_order.html')


