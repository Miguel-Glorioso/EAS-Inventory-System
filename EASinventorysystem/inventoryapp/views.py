from django.shortcuts import render, redirect, get_object_or_404
from . models import Product, Category, Account
from django.http import HttpResponseRedirect

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
    return render(request, 'inventoryapp/current_inventory.html', {'product':all_inventory})


def add_product(request):
    if request.method == 'POST':
        Product_Name = request.POST.get('product_name')
        Product_Price = request.POST.get('product_price')
        EAS_Product_ID = request.POST.get('eas_id')
        Product_SKU = request.POST.get('product_sku')
        Product_Initial_Count = request.POST.get('product_initial_count')
        Product_Picture = request.FILES.get('product_picture') 
        Product_Category = request.POST.get('product_category')
        Product_Stock_threshold = request.POST.get("product_stock_level_threshold")
        Product_Tag = request.POST.get('product_tags')
        
        if Product_Stock_threshold == 0:
              Product_Stock_threshold = None
        
        Product.objects.create(
            EAS_Product_ID=EAS_Product_ID,
            Name=Product_Name,
            Picture=Product_Picture,
            SKU=Product_SKU,
            Price=Product_Price,
            Actual_Inventory_Count=Product_Initial_Count,
            Reserved_Inventory_Count=0,
            To_Be_Received_Inventory_Count=0,
            Visibility=True,
            Product_Low_Stock_Threshold = Product_Stock_threshold, 
        )
        return redirect('current_inventory')
    else:
        return render(request, 'inventoryapp/add_product.html')


def view_product(request, pk):
    p = get_object_or_404(Product, pk=pk)
    print("CHECK THIS", p)
    return render(request, 'inventoryapp/view_product.html', {'p':p})
