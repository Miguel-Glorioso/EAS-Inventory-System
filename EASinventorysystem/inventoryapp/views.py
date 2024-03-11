from django.shortcuts import render, redirect, get_object_or_404
from . models import Product, Category, Account, Consignee, Consignee_Product, Purchase_Order, Product_Ordered, Customer
from django.http import  JsonResponse
from django.core.files.storage import default_storage
from django.core.files import File

from django.http import HttpResponse



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


def view_product(product_pk):
    try:
        product = Product.objects.get(pk=product_pk)
        con_p = Consignee_Product.objects.filter(Product_ID=product_pk)
        response_data = {
            'name': product.Name,
            'id': product.EAS_Product_ID,
            'sku': product.SKU,
            'price': product.Price,
            'count': product.Actual_Inventory_Count,
            'category': product.Category.Category_Name,
            'tags': [consignee_product.Consignee_ID.Customer_Name for consignee_product in con_p], 
            'threshold': product.Product_Low_Stock_Threshold,
            'picture': product.Picture.url if product.Picture else None,
        }
        return JsonResponse(response_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

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
    return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders})

def add_purchase_order(request):
    if request.method == 'POST':
        print("start")
        Requested_Date = request.POST.get('requested_date')
        Customer_Type = request.POST.get('customer_type')
        Customer_Name = request.POST.get('customer_name')
        Shipping_Method = request.POST.get('shipping_method')
        Order_Method = request.POST.get('order_method')
        Primary_Contact = request.POST.get('primary_contact')
        Email_Address = request.POST.get('email_address')
        Emergency_Contact = request.POST.get('emergency_contact')
        Address_Line1 = request.POST.get('address_line1')
        Province = request.POST.get('province')
        Municipality = request.POST.get('municipality')
        Barangay = request.POST.get('barangay')
        Zip_Code = request.POST.get('zip_code')
        Notes = request.POST.get('notes')
        #Products = request.POST.getlist('sampleproduct') This should contain the list of product ids in the PO and quantity split by -
        #product and quantity can also be shown in a diff way this is just the first one i thought of
        PO_customer = None
        PO_consignee = None

        #Checks customer type
        print(Customer_Type)
        if Customer_Type == "Consignee":
            print('Ctypecheck: CON')
            existing_consignee = Consignee.objects.filter(
                Customer_Name = Customer_Name,
                Primary_Contact_Number = Primary_Contact,
                Email_Address = Email_Address,
                Emergency_Contact_Number = Emergency_Contact,
                Address_Line_1 = Address_Line1,
                Province = Province,
                Municipality = Municipality,
                Barangay = Barangay,
                Zip_Code = Zip_Code
            )
            #Checks if consignee already exists
            if existing_consignee:
                print('CONexistCHECK: yes')
                PO_consignee = existing_consignee.first()

            else:
                print('CONexistCHECK: no')
                PO_consignee = Consignee.objects.create(
                    Customer_Name = Customer_Name,
                    Primary_Contact_Number = Primary_Contact,
                    Customer_Type = Customer_Type,
                    Email_Address = Email_Address,
                    Emergency_Contact_Number = Emergency_Contact,
                    Address_Line_1 = Address_Line1,
                    Province = Province,
                    Municipality = Municipality,
                    Barangay = Barangay,
                    Zip_Code = Zip_Code,
                    Notes = Notes
                )

        elif Customer_Type == 'Direct':
            print('Ctypecheck: DIR')
            existing_customer = Customer.objects.filter(
                Customer_Name = Customer_Name,
                Primary_Contact_Number = Primary_Contact,
                Address_Line_1 = Address_Line1,
                Province = Province,
                Municipality = Municipality,
                Barangay = Barangay,
                Zip_Code = Zip_Code
            )

            #Checks if customer already exists
            if existing_customer:
                print('CUSTExistCHECK: YES')
                PO_customer = existing_customer.first()
                
            else:
                print('CUSTExistCHECK: NO')
                PO_customer = Customer.objects.create(
                    Customer_Name = Customer_Name,
                    Primary_Contact_Number = Primary_Contact,
                    Customer_Type = Customer_Type,
                    Address_Line_1 = Address_Line1,
                    Province = Province,
                    Municipality = Municipality,
                    Barangay = Barangay,
                    Zip_Code = Zip_Code,
                    Notes = Notes
                )
        print("create po")  
        PO = Purchase_Order.objects.create(
                Requested_Date=Requested_Date,
                Shipping_Method=Shipping_Method,
                Order_Method=Order_Method,
                Consignee_ID=PO_consignee,
                Customer_ID=PO_customer,
                #Account_ID=PO_account,
                Total_Due=10000,
                Notes=Notes,
                )
        
        # this is to make the associative entities Product_Ordered
        #for p_id in Products:
        #    p_id.split('-')
        #    p = Product.objects.get(pk=p_id[0])
        #    Product_Ordered.objects.create(
        #        Purchase_Order_ID = PO,
        #        Product_ID = p,
        #        quantity = p_id[1]
        #    )
        return redirect('current_pos')

    else:
        return render(request, 'inventoryapp/add_po.html')

def view_po(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
    return render(request, 'inventoryapp/view_po.html', {'po':purchase_order, 'products':products_ordered})

def close_po(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)

    for product in products_ordered:
        product_listing = Product.objects.get(Product_ID=product.Product_ID.Product_ID)
        print(product_listing.Actual_Inventory_Count)
        product_listing.Actual_Inventory_Count -= product.Quantity
        product_listing.Reserved_Inventory_Count -= product.Quantity
        product_listing.save()
        print(product_listing.Actual_Inventory_Count)

    purchase_order.PO_Status = 'Closed'
    purchase_order.Progress = 'Shipped'
    purchase_order.save()
    
    return redirect('current_pos')