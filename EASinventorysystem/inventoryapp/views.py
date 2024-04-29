from django.shortcuts import render, redirect, get_object_or_404
from . models import Product, Category, Account, Consignee, Consignee_Product, Purchase_Order, Product_Ordered, Customer, Product_Requisition_Order, Stock_Ordered
from django.http import  JsonResponse
import json
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils import timezone
from datetime import datetime
from itertools import chain
from django.contrib.auth import authenticate, login, logout



# Create your views here.

def account_login(request):
    if request.method == 'POST':
        login_username = request.POST.get('user_name')
        login_password = request.POST.get('password')
        user = authenticate(request, username=login_username, password=login_password)
        if user is not None:
            login(request, user)
            return redirect('current_inventory')
        else:
            error_msg = "Invalid Username/Password"
            return render(request, 'inventoryapp/login.html', {'error_msg': error_msg})
    else:
        return render(request, 'inventoryapp/login.html')

def inventory_list(request):
    all_inventory = Product.objects.all()
    all_consignee_products = Consignee_Product.objects.all()
    all_categories = Category.objects.all()
    all_consignees = Consignee.objects.all()
    show_hidden = False
    
    category_param = request.GET.get('category')
    consignee_param = request.GET.get('consignee')
    hidden_param = request.GET.get('showHidden')

    if hidden_param:
        show_hidden = True

    if category_param:
         
        category = get_object_or_404(Category, Category_ID=category_param)
        all_inventory = all_inventory.filter(Category=category)

    if consignee_param:
        consignee = get_object_or_404(Consignee, Consignee_ID=consignee_param)
        consignee_products = all_consignee_products.filter(Consignee_ID=consignee)
        product_ids = consignee_products.values_list('Product_ID', flat=True)
        all_inventory = all_inventory.filter(Product_ID__in=product_ids)
    return render(request, 'inventoryapp/current_inventory.html', {'products':all_inventory, 'categories':all_categories, 'consignees':all_consignees, 'consignee_products':all_consignee_products, 'show_hidden':show_hidden})

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

        product_category = get_object_or_404(Category, pk=Product_Category)

        if int(Product_Stock_threshold) == 0:
            print('no prod stock')
            Product_Stock_threshold = None

            if int(Product_Initial_Count) == 0:
                Stock_Status = 'No Stock'
            elif int(Product_Initial_Count) <= int(product_category.Category_Product_Low_Stock_Threshold):
                Stock_Status = 'Low Stock'
            else:
                Stock_Status = 'Regular Stock'
        else:
            print('yes prod stock')
            if int(Product_Initial_Count) == 0:
                Stock_Status = 'No Stock'
            elif int(Product_Initial_Count) <= int(Product_Stock_threshold):
                Stock_Status = 'Low Stock'
            else:
                Stock_Status = 'Regular Stock'
        
        existing_product_name = Product.objects.filter(
            Name = Product_Name
        )
        existing_product_ID = Product.objects.filter(
            EAS_Product_ID = EAS_Product_ID
        )

        if existing_product_name:
            error_msg = 'Product Already Exists'
            return render(request, 'inventoryapp/add_product.html',  {'categories': categories, 'consignees': consignees, 'error_msg': error_msg})

        elif existing_product_ID:
            error_msg = 'Product ID Already Exists'
            return render(request, 'inventoryapp/add_product.html',  {'categories': categories, 'consignees': consignees, 'error_msg': error_msg})
           
        else:
            
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
                Product_Stock_Status = Stock_Status,
                Category = product_category
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

def view_product(request, product_pk):
    try:
        product = Product.objects.get(pk=product_pk)
        con_p = Consignee_Product.objects.filter(Product_ID=product_pk)
        response_data = {
            'product_id' : product.Product_ID,
            'name': product.Name,
            'id': product.EAS_Product_ID,
            'sku': product.SKU,
            'price': product.Price,
            'count': product.Actual_Inventory_Count,
            'category': product.Category.Category_Name,
            'tags': [consignee_product.Consignee_ID.Consignee_Name for consignee_product in con_p], 
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

        category = Category.objects.get(Category_ID = Product_Category)
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
        
        if int(product.Actual_Inventory_Count) == 0:
            Stock_Status = 'No Stock'
        elif int(product.Actual_Inventory_Count) <= int(Product_Stock_threshold):
            Stock_Status = 'Low Stock'
        else:
            Stock_Status = 'Regular Stock'

        if int(Product_Stock_threshold) == 0:
            Product_Stock_threshold = None

            if int(product.Actual_Inventory_Count) == 0:
                Stock_Status = 'No Stock'
            elif int(product.Actual_Inventory_Count) <= int(category.Category_Product_Low_Stock_Threshold):
                Stock_Status = 'Low Stock'
            else:
                Stock_Status = 'Regular Stock'
        else:
            if int(product.Actual_Inventory_Count) == 0:
                Stock_Status = 'No Stock'
            elif int(product.Actual_Inventory_Count) <= int(Product_Stock_threshold):
                Stock_Status = 'Low Stock'
            else:
                Stock_Status = 'Regular Stock'

        Product.objects.filter(pk=pk).update(
            EAS_Product_ID=EAS_Product_ID,
            Name=Product_Name,
            SKU=Product_SKU,
            Price=Product_Price,
            Visibility=Product_Visibility,
            Product_Low_Stock_Threshold=Product_Stock_threshold,
            Product_Stock_Status=Stock_Status,
            Category= category  
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
        
        
        return redirect('current_inventory')
    else:
        return render(request, 'inventoryapp/update_product.html', {'p':p, 'con_p':con_p, 'con_p_ids':con_p_ids, 'categories': categories,  'consignees': consignees})
    
def purchase_order_list(request):
    all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
    return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders})

def update_PO_progress(request, PO_pk):
    if request.method == 'POST':
        data = json.loads(request.body)
        progress = data.get('progress')

        try:
            purchase_order = Purchase_Order.objects.get(pk=PO_pk)
            purchase_order.Progress = progress
            purchase_order.save()

            return JsonResponse({'message': 'Progress updated successfully'})
        except Purchase_Order.DoesNotExist:
            return JsonResponse({'error': 'Purchase Order does not exist'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

# def add_purchase_order(request):
#     products = Product.objects.all()
#     if request.method == 'POST':
#         Requested_Date = request.POST.get('requested_date')
#         Customer_Type = request.POST.get('customer_type')
#         Name = request.POST.get('customer_name')
#         Shipping_Method = request.POST.get('shipping_method')
#         Order_Method = request.POST.get('order_method')
#         Primary_Contact = request.POST.get('primary_contact')
#         Email_Address = request.POST.get('email_address')
#         Emergency_Contact = request.POST.get('emergency_contact')
#         Address_Line1 = request.POST.get('address_line1')
#         Province = request.POST.get('province')
#         Municipality = request.POST.get('municipality')
#         Barangay = request.POST.get('barangay')
#         Zip_Code = request.POST.get('zip_code')
#         Notes = request.POST.get('c_notes')
#         Products = request.POST.get('all_products')
#         Total_Price = request.POST.get('total_price')
#         PO_customer = None
#         PO_consignee = None
#         print(Products, Total_Price)

#         #Checks customer type
#         if Customer_Type == "Consignee":
#             existing_consignee = Consignee.objects.filter(
#                 Consignee_Name = Name,
#                 Primary_Contact_Number = Primary_Contact,
#                 Email_Address = Email_Address,
#                 Emergency_Contact_Number = Emergency_Contact,
#                 Address_Line_1 = Address_Line1,
#                 Province = Province,
#                 Municipality = Municipality,
#                 Barangay = Barangay,
#                 Zip_Code = Zip_Code
#             )
#             #Checks if consignee already exists
#             if existing_consignee:
#                 print('CONexistCHECK: yes')
#                 PO_consignee = existing_consignee.first()

#             else:
#                 print('CONexistCHECK: no')
#                 PO_consignee = Consignee.objects.create(
#                     Consignee_Name = Name,
#                     Primary_Contact_Number = Primary_Contact,
#                     Customer_Type = Customer_Type,
#                     Email_Address = Email_Address,
#                     Emergency_Contact_Number = Emergency_Contact,
#                     Address_Line_1 = Address_Line1,
#                     Province = Province,
#                     Municipality = Municipality,
#                     Barangay = Barangay,
#                     Zip_Code = Zip_Code,
#                     Notes = Notes
#                 )

#         elif Customer_Type == 'Direct':
#             existing_customer = Customer.objects.filter(
#                 Customer_Name = Name,
#                 Primary_Contact_Number = Primary_Contact,
#                 Address_Line_1 = Address_Line1,
#                 Province = Province,
#                 Municipality = Municipality,
#                 Barangay = Barangay,
#                 Zip_Code = Zip_Code
#             )

#             #Checks if customer already exists
#             if existing_customer:
#                 PO_customer = existing_customer.first()
                
#             else:
#                 PO_customer = Customer.objects.create(
#                     Customer_Name = Name,
#                     Primary_Contact_Number = Primary_Contact,
#                     Customer_Type = Customer_Type,
#                     Address_Line_1 = Address_Line1,
#                     Province = Province,
#                     Municipality = Municipality,
#                     Barangay = Barangay,
#                     Zip_Code = Zip_Code,
#                     Notes = Notes
#                 )
#         current_date = timezone.now()

#         PO = Purchase_Order.objects.create(
#                 Requested_Date=Requested_Date,
#                 Creation_Date = current_date,
#                 Shipping_Method=Shipping_Method,
#                 Order_Method=Order_Method,
#                 Consignee_ID=PO_consignee,
#                 Customer_ID=PO_customer,
#                 #Account_ID=PO_account,
#                 Total_Due=Total_Price,
#                 Notes=Notes,
#                 )
        
#         Products = Products[:-1]
#         Ordered_Products= Products.split("-")

#         for op in Ordered_Products:
#             values = op.split(":")
#             product_object = Product.objects.get(Product_ID = values[0])
#             print(product_object, product_object.Reserved_Inventory_Count)

#             product_object.Reserved_Inventory_Count += int(values[1])
#             product_object.save()


#             Product_Ordered.objects.create(Product_ID = product_object, Purchase_Order_ID = PO, Quantity = values[1])

#         return redirect('current_pos')

#     else:
#         return render(request, 'inventoryapp/add_po.html', {'products': products})

def add_purchase_order_consignee(request):
    all_products = Product.objects.all()
    all_consignees = Consignee.objects.all()
    # all_consignees = Consignee.objects.all()
    if request.method == 'POST':
        Requested_Date = request.POST.get('requested_date')
        Order_Notes = request.POST.get('order_notes')
        Products = request.POST.get('all_products')
        Total_Price = request.POST.get('total_price')
        Shipping_Method = request.POST.get('shipping_method')
        Order_Method = request.POST.get('order_method')
        PO_Consignee = request.POST.get('consignee')
        PO_account = request.POST.get('account')

        PO_Consignee = get_object_or_404(Consignee, Consignee_ID=PO_Consignee)
        PO_account = get_object_or_404(Account,pk=PO_account)
        if Requested_Date == '':
            Requested_Date = None

        # if Order_Method == None:
        #     Order_Method = "No selected order method"
        
        current_date = timezone.now()
        PO = Purchase_Order.objects.create(
            Requested_Date=Requested_Date,
            Creation_Date=current_date,
            Shipping_Method=Shipping_Method,
            Order_Method=Order_Method,
            Consignee_ID=PO_Consignee,
            Account_ID_Created_by=PO_account,
            Total_Due=Total_Price,
            Notes=Order_Notes,
            )
        
        Products = Products[:-1]
        Ordered_Products= Products.split("-")

        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            product_object.Reserved_Inventory_Count += int(values[1])
            product_object.save()

            Product_Ordered.objects.create(Product_ID=product_object, Purchase_Order_ID=PO, Quantity=values[1])

        return redirect('current_pos')
    
    else:
        return render(request, 'inventoryapp/add_po_consignee.html', {'products': all_products, 'consignees':all_consignees})

def add_purchase_order_direct_customer(request):
    products = Product.objects.all()
    if request.method == 'POST':
        Requested_Date = request.POST.get('requested_date')
        Customer_Name = request.POST.get('customer_name')
        Shipping_Method = request.POST.get('shipping_method')
        Order_Method = request.POST.get('order_method')
        Primary_Contact = request.POST.get('contact_info')
        Address_Line1 = request.POST.get('address_line1')
        Province = request.POST.get('province')
        Municipality = request.POST.get('municipality')
        Barangay = request.POST.get('barangay')
        Zip_Code = request.POST.get('zip_code')
        Customer_Notes = request.POST.get('customer_notes')
        Order_Notes = request.POST.get('order_notes')
        Products = request.POST.get('all_products')
        Total_Price = request.POST.get('total_price')
        PO_account = request.POST.get('account')
        print(Order_Method)
        
        PO_account = get_object_or_404(Account,pk=PO_account)
        

        print(Order_Method)
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
            PO_customer = existing_customer.first()
            PO_customer.Notes = Customer_Notes
            PO_customer.save()
            
            
        else:
        #creates a new direct customer
            PO_customer = Customer.objects.create(
                Customer_Name = Customer_Name,
                Primary_Contact_Number = Primary_Contact,
                Customer_Type = 'Direct',
                Address_Line_1 = Address_Line1,
                Province = Province,
                Municipality = Municipality,
                Barangay = Barangay,
                Zip_Code = Zip_Code,
                Notes = Customer_Notes
                )
        
        # PO creation
        current_date = timezone.now()
        
        PO = Purchase_Order.objects.create(
                Requested_Date=Requested_Date,
                Creation_Date=current_date,
                Shipping_Method=Shipping_Method,
                Order_Method=Order_Method,
                Customer_ID=PO_customer,
                Account_ID_Created_by=PO_account,
                Total_Due=Total_Price,
                Notes=Order_Notes,
                )
        
        Products = Products[:-1]
        Ordered_Products= Products.split("-")

        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            product_object.Reserved_Inventory_Count += int(values[1])
            product_object.save()

            Product_Ordered.objects.create(Product_ID=product_object, Purchase_Order_ID=PO, Quantity=values[1])

        return redirect('current_pos')
    else:

        return render(request, 'inventoryapp/add_po_direct_customer.html', {'products': products})


# def add_po_second(request):
#     products = Product.objects.all()
#     return render(request, 'inventoryapp/add_po_second.html', {'products': products})

def view_po(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
    return render(request, 'inventoryapp/view_po.html', {'po':purchase_order, 'products':products_ordered})

def close_po(request, pk, account_id):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if purchase_order.PO_Status != 'Closed':
        products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)

        Sufficient_Stock = True
        for product in products_ordered:
            product_listing = Product.objects.get(Product_ID=product.Product_ID.Product_ID)
            if product_listing.Actual_Inventory_Count < product.Quantity:
                Sufficient_Stock = False
        
        if Sufficient_Stock:

            for product in products_ordered:
                product_listing = Product.objects.get(Product_ID=product.Product_ID.Product_ID) #this is the actual product not the product ordered
                product_listing.Actual_Inventory_Count -= product.Quantity #product inventory count gets deducted
                product_listing.Reserved_Inventory_Count -= product.Quantity #product reserved invetory count gets deducted

                #have not yet been checked
                if product_listing.Product_Low_Stock_Threshold:

                    if int(product_listing.Actual_Inventory_Count) == 0: 
                        product_listing.Product_Stock_Status = 'No Stock'
                    elif int(product_listing.Actual_Inventory_Count) <= int(product_listing.Product_Low_Stock_Threshold):
                        product_listing.Product_Stock_Status = 'Low Stock'

                else:
                    if int(product_listing.Actual_Inventory_Count) == 0: 
                        product_listing.Product_Stock_Status = 'No Stock'
                    elif int(product_listing.Actual_Inventory_Count) <= int(product_listing.Category.Category_Product_Low_Stock_Threshold):
                        product_listing.Product_Stock_Status = 'Low Stock'
                
                print(product_listing.Product_Stock_Status)

                product_listing.save()

            purchase_order.Fulfilled_Date = timezone.now()
            purchase_order.PO_Status = 'Closed'
            purchase_order.Progress = 'Shipped'
            purchase_order.Account_ID_Closed_by = account
            purchase_order.save()
        
        else:
            error_msg = 'Sufficient Stock for Purchase Order'
            all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
            return render(request, 'inventoryapp/current_pos.html', {'error_msg':error_msg, 'purchase_orders':all_purchase_orders})
            
    return redirect('current_pos')

def requisition_order_list(request):
    all_requisition_orders = Product_Requisition_Order.objects.all()
    return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders})

def update_PRO_progress(request, PRO_pk):
    if request.method == 'POST':
        data = json.loads(request.body)
        progress = data.get('progress')

        try:
            purchase_order = Product_Requisition_Order.objects.get(pk=PRO_pk)
            
            purchase_order.Progress = progress
            purchase_order.save()

            return JsonResponse({'message': 'Progress updated successfully'})
        except Purchase_Order.DoesNotExist:
            return JsonResponse({'error': 'Purchase Order does not exist'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

def add_requisition_order(request):
    products = Product.objects.all()
    if request.method == 'POST':
        estimated_receiving_date = request.POST.get('estimated_receiving_date')
        manufacturer_name = request.POST.get('manufacturer_name')
        total_cost =  request.POST.get('total_cost')
        pro_notes = request.POST.get('pro_notes')
        Products = request.POST.get('all_products')
        PRO_account = request.POST.get('account')
        
        
        PRO_account = get_object_or_404(Account, pk=PRO_account)

        current_date = timezone.now()
        
        PRO = Product_Requisition_Order.objects.create(
            Estimated_Receiving_Date=estimated_receiving_date,
            Creation_Date=current_date,
            PRO_Manufacturer=manufacturer_name,
            Total_Cost=total_cost,
            Account_ID_Created_by = PRO_account,
            Notes=pro_notes,
        )

        Products = Products[:-1]
        Ordered_Products= Products.split("-")

        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            product_object.To_Be_Received_Inventory_Count += int(values[1])
            product_object.save()

            Stock_Ordered.objects.create(Product_ID=product_object, Product_Requisition_ID=PRO, Quantity=values[1])

        return redirect('current_pros')
    else:
        return render(request, 'inventoryapp/add_pro.html', {'products': products})

def update_pro(request, pk):
    requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    products = Product.objects.all()
    stock_ordered_items = Stock_Ordered.objects.filter(Product_Requisition_ID=requisition_order)
    print(stock_ordered_items)

    if request.method == 'POST':
        estimated_receiving_date = request.POST.get('estimated_receiving_date')
        manufacturer_name = request.POST.get('manufacturer_name')
        total_cost =  request.POST.get('total_cost')
        pro_notes = request.POST.get('pro_notes')
        Products = request.POST.get('all_products')
        
        current_date = timezone.now()
        
        # Update the requisition order object with the new data
        requisition_order.Estimated_Receiving_Date = estimated_receiving_date
        requisition_order.Creation_Date = current_date
        requisition_order.PRO_Manufacturer = manufacturer_name
        requisition_order.Total_Cost = total_cost
        requisition_order.Notes = pro_notes
        
        requisition_order.save()

        # Process the ordered products
        Products = Products[:-1]
        Ordered_Products = Products.split("-")
        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            # Update To_Be_Received_Inventory_Count for the product
            product_object.To_Be_Received_Inventory_Count += int(values[1])
            product_object.save()

            # Update or create a Stock_Ordered object for the product requisition order
            stock_ordered, _ = Stock_Ordered.objects.get_or_create(
                Product_ID=product_object,
                Product_Requisition_ID=requisition_order
            )
            stock_ordered.Quantity = values[1]
            stock_ordered.save()

        return redirect('current_pros')
    else:
        
        return render(request, 'inventoryapp/update_pro.html', {'requisition_order': requisition_order, 'products': products, 'stock_ordered_items': stock_ordered_items})
    
def view_pro(request, pk):
    product_requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID = pk)
    return render(request, 'inventoryapp/view_pro.html', {'pro':product_requisition_order, 'stocks':stocks_ordered})

def close_pro(request, pk, account_id):
    requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if requisition_order.PRO_Status != 'Closed':
        stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)

        for stock in stocks_ordered:
            stock_listing = Product.objects.get(Product_ID=stock.Product_ID.Product_ID) #this is the actual product not the product ordered
            stock_listing.Actual_Inventory_Count += stock.Quantity #product inventory count gets deducted
            stock_listing.To_Be_Received_Inventory_Count -= stock.Quantity #product reserved invetory count gets deducted

            #have not yet been checked
            if stock_listing.Product_Low_Stock_Threshold:

                if int(stock_listing.Actual_Inventory_Count) <= int(stock_listing.Product_Low_Stock_Threshold):
                    stock_listing.Product_Stock_Status = 'Low Stock'
                else:
                    stock_listing.Product_Stock_Status = 'Regular Stock'

            else:
                if int(stock_listing.Actual_Inventory_Count) <= int(stock_listing.Category.Category_Product_Low_Stock_Threshold):
                    stock_listing.Product_Stock_Status = 'Low Stock'
                else:
                    stock_listing.Product_Stock_Status = 'Regular Stock'
                    
            
            print(stock_listing.Product_Stock_Status)

            stock_listing.save()

        requisition_order.Received_Date = timezone.now()
        requisition_order.PRO_Status = 'Closed'
        requisition_order.Progress = 'To be Picked Up'
        requisition_order.Account_ID_Closed_by = account
        requisition_order.save()
    
    return redirect('current_pros')


def customer_list(request):
    all_direct = Customer.objects.all()
    all_consignees = Consignee.objects.all()
    all_customers = chain(all_direct, all_consignees)

    customer_type_param = request.GET.get('customer_type')

    if customer_type_param:
        if customer_type_param == "Direct":
            all_customers = Customer.objects.all()
        elif customer_type_param == "Consignee":
            all_customers = Consignee.objects.all()
            
    return render(request, 'inventoryapp/current_customers.html', {'customers':all_customers    })

def create_direct_customer(request):
    if request.method == 'POST':
        Customer_Name = request.POST.get('customer_name')
        Primary_Contact_Number = request.POST.get('primary_contact_number')
        Address_Line_1 = request.POST.get('address_line1')
        Province = request.POST.get('province')
        Municipality = request.POST.get('municipality')
        Barangay = request.POST.get('barangay')
        Zip_Code = request.POST.get('zip_code')
        Notes = request.POST.get('notes')

        existing_customer = Customer.objects.filter(
            Customer_Name=Customer_Name,
            Primary_Contact_Number=Primary_Contact_Number,
            Address_Line_1=Address_Line_1,
            Province=Province,
            Municipality=Municipality,
            Barangay=Barangay,
            Zip_Code=Zip_Code
        )
        if existing_customer:
            error_msg = 'Customer Already Exists'
            return render(request, 'inventoryapp/create_direct_customer.html',  {'error_msg': error_msg})

        # If customer doesn't exist, create a new one
        else:
            # Create a new customer object
            Customer.objects.create(
                Customer_Name=Customer_Name,
                Customer_Type='Direct',
                Primary_Contact_Number=Primary_Contact_Number,
                Address_Line_1=Address_Line_1,
                Province=Province,
                Municipality=Municipality,
                Barangay=Barangay,
                Zip_Code=Zip_Code,
                Notes=Notes
            )

            return redirect('current_customers')
    else:
        return render(request, 'inventoryapp/create_direct_customer.html')

def create_consignee(request):
    if request.method == 'POST':
        Consignee_Tag_ID = request.POST.get('consignee_tag_id')
        Consignee_Name = request.POST.get('consignee_name')
        Address_Line_1 = request.POST.get('address_line_1')
        Barangay = request.POST.get('barangay')
        Municipality = request.POST.get('municipality')
        Province = request.POST.get('province')
        Zip_Code = request.POST.get('zip_code')
        Primary_Contact_Number = request.POST.get('primary_contact_number')
        Notes = request.POST.get('notes')
        Consignment_Period_Start = request.POST.get('consignment_period_start')
        Consignment_Period_End = request.POST.get('consignment_period_end')
        Emergency_Contact_Number = request.POST.get('emergency_contact_number')
        Email_Address = request.POST.get('email_address')
        Tag_Hex_Color_ID = request.POST.get('tag_hex_color_id')

        # Check if the consignee already exists
        existing_consignee = Consignee.objects.filter(
            Consignee_Tag_ID=Consignee_Tag_ID,
            Consignee_Name=Consignee_Name,
        )
        if existing_consignee:
            error_msg = 'Consignee Already Exists'
            return render(request, 'inventoryapp/create__consignee.html',  {'error_msg': error_msg})


        else:   
            # Create a new consignee object
            Consignee.objects.create(
                Consignee_Tag_ID=Consignee_Tag_ID,
                Consignee_Name=Consignee_Name,
                Address_Line_1=Address_Line_1,
                Barangay=Barangay,
                Municipality=Municipality,
                Province=Province,
                Zip_Code=Zip_Code,
                Primary_Contact_Number=Primary_Contact_Number,
                Customer_Type= 'Consignee',
                Notes=Notes,
                Consignment_Period_Start=Consignment_Period_Start,
                Consignment_Period_End=Consignment_Period_End,
                Emergency_Contact_Number=Emergency_Contact_Number,
                Email_Address=Email_Address,
                Tag_Hex_Color_ID=Tag_Hex_Color_ID
            )

            # Redirect to some page after successful creation
            return redirect('categories_consignee_tags')

    else:
        return render(request, 'inventoryapp/create_consignee.html')
    
def create__consignee(request):
    if request.method == 'POST':
        Consignee_Tag_ID = request.POST.get('consignee_tag_id')
        Consignee_Name = request.POST.get('consignee_name')
        Address_Line_1 = request.POST.get('address_line_1')
        Barangay = request.POST.get('barangay')
        Municipality = request.POST.get('municipality')
        Province = request.POST.get('province')
        Zip_Code = request.POST.get('zip_code')
        Primary_Contact_Number = request.POST.get('primary_contact_number')
        Notes = request.POST.get('notes')
        Consignment_Period_Start = request.POST.get('consignment_period_start')
        Consignment_Period_End = request.POST.get('consignment_period_end')
        Emergency_Contact_Number = request.POST.get('emergency_contact_number')
        Email_Address = request.POST.get('email_address')
        Tag_Hex_Color_ID = request.POST.get('tag_hex_color_id')

        # Check if the consignee already exists
        existing_consignee = Consignee.objects.filter(
            Consignee_Tag_ID=Consignee_Tag_ID,
            Consignee_Name=Consignee_Name,
        )
        if existing_consignee:
            error_msg = 'Consignee Already Exists'
            return render(request, 'inventoryapp/create_consignee.html',  {'error_msg': error_msg})


        else:   
            # Create a new consignee object
            Consignee.objects.create(
                Consignee_Tag_ID=Consignee_Tag_ID,
                Consignee_Name=Consignee_Name,
                Address_Line_1=Address_Line_1,
                Barangay=Barangay,
                Municipality=Municipality,
                Province=Province,
                Zip_Code=Zip_Code,
                Primary_Contact_Number=Primary_Contact_Number,
                Customer_Type= 'Consignee',
                Notes=Notes,
                Consignment_Period_Start=Consignment_Period_Start,
                Consignment_Period_End=Consignment_Period_End,
                Emergency_Contact_Number=Emergency_Contact_Number,
                Email_Address=Email_Address,
                Tag_Hex_Color_ID=Tag_Hex_Color_ID
            )

            # Redirect to some page after successful creation
            return redirect('categories_consignee_tags')

    else:
        return render(request, 'inventoryapp/create_consignee.html')

def view_customer(request, customer_type, customer_id):
    try:
        if customer_type == 'direct':
            customer_model = Customer
        elif customer_type == 'consignee':
            customer_model = Consignee
        else:
            return JsonResponse({'error': 'Invalid customer type'}, status=400)

        customer = get_object_or_404(customer_model, pk=customer_id)

        response_data = {
            'customer_id': customer.Customer_ID if hasattr(customer, 'Customer_ID') else customer.Consignee_ID,
            'name': customer.Customer_Name if hasattr(customer, 'Customer_Name') else customer.Consignee_Name,
            'address': customer.Address_Line_1,
            'barangay': customer.Barangay,
            'municipality': customer.Municipality,
            'province': customer.Province,
            'zip_code': customer.Zip_Code,
            'contact_number': customer.Primary_Contact_Number,
            'customer_type': customer.Customer_Type,
            'notes': customer.Notes,
        }
        if customer_type == 'consignee':
            response_data.update({
                'consignment_period_start': customer.Consignment_Period_Start,
                'consignment_period_end': customer.Consignment_Period_End,
                'emergency_contact_number': customer.Emergency_Contact_Number,
                'email_address': customer.Email_Address,
                'tag_hex_color_id': customer.Tag_Hex_Color_ID,
            })
        return JsonResponse(response_data)
    
    except (Customer.DoesNotExist, Consignee.DoesNotExist):
        return JsonResponse({'error': 'Customer not found'}, status=404)
    
def update_direct_customer(request, pk):
    customer = get_object_or_404(Customer, Customer_ID=pk)

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        primary_contact_number = request.POST.get('primary_contact_number')
        address_line1 = request.POST.get('address_line1')
        province = request.POST.get('province')
        municipality = request.POST.get('municipality')
        barangay = request.POST.get('barangay')
        zip_code = request.POST.get('zip_code')
        notes = request.POST.get('notes')

        customer.Customer_Name = customer_name
        customer.Primary_Contact_Number = primary_contact_number
        customer.Address_Line_1 = address_line1
        customer.Province = province
        customer.Municipality = municipality
        customer.Barangay = barangay
        customer.Zip_Code = zip_code
        customer.Notes = notes

        customer.save()

        return redirect('current_customers')
    else:
        return render(request, 'inventoryapp/update_direct_customer.html', {'customer': customer})
    
def update_consignee(request, pk):
    consignee = get_object_or_404(Consignee, pk=pk)
    Start_date = consignee.Consignment_Period_Start
    End_date = consignee.Consignment_Period_End

    Start_date_string = Start_date.strftime('%Y-%m-%d')
    End_date_string = End_date.strftime('%Y-%m-%d')
    if request.method == 'POST':
        Consignee_Tag_ID = request.POST.get('consignee_tag_id')
        Consignee_Name = request.POST.get('consignee_name')
        Address_Line_1 = request.POST.get('address_line_1')
        Barangay = request.POST.get('barangay')
        Municipality = request.POST.get('municipality')
        Province = request.POST.get('province')
        Zip_Code = request.POST.get('zip_code')
        Primary_Contact_Number = request.POST.get('primary_contact_number')
        Notes = request.POST.get('notes')
        Consignment_Period_Start = request.POST.get('consignment_period_start')
        Consignment_Period_End = request.POST.get('consignment_period_end')
        Emergency_Contact_Number = request.POST.get('emergency_contact_number')
        Email_Address = request.POST.get('email_address')
        Tag_Hex_Color_ID = request.POST.get('tag_hex_color_id')

        # Update the consignee object
        consignee.Consignee_Tag_ID = Consignee_Tag_ID
        consignee.Consignee_Name = Consignee_Name
        consignee.Address_Line_1 = Address_Line_1
        consignee.Barangay = Barangay
        consignee.Municipality = Municipality
        consignee.Province = Province
        consignee.Zip_Code = Zip_Code
        consignee.Primary_Contact_Number = Primary_Contact_Number
        consignee.Notes = Notes
        consignee.Consignment_Period_Start = Consignment_Period_Start
        consignee.Consignment_Period_End = Consignment_Period_End
        consignee.Emergency_Contact_Number = Emergency_Contact_Number
        consignee.Email_Address = Email_Address
        print(Tag_Hex_Color_ID,'CHECKIS')
        consignee.Tag_Hex_Color_ID = Tag_Hex_Color_ID

        consignee.save()

        return redirect('current_customers')

    else:
        return render(request, 'inventoryapp/update_consignee.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string})

def update_PO_direct_customer(request, po_pk, c_pk):
    PO = get_object_or_404(Purchase_Order, pk=po_pk)
    products_ordered =  Product_Ordered.objects.filter(Purchase_Order_ID=po_pk)
    products = Product.objects.all()
    if request.method == 'POST':
        print("WIP")
    else:
        return render(request, 'inventoryapp/update_po_direct_customer.html', {'PO':PO, 'products_ordered':products_ordered, 'products':products})

def update_PO_consignee(request, po_pk, c_pk):
    PO = get_object_or_404(Purchase_Order, pk=po_pk)
    all_consignees = Consignee.objects.all()
    products_ordered =  Product_Ordered.objects.filter(Purchase_Order_ID=po_pk)
    products = Product.objects.all() 
    if request.method == 'POST':
        print("WIP")
    else:
        return render(request, 'inventoryapp/update_po_consignee.html', {'PO':PO, 'products_ordered':products_ordered, 'products':products, 'consignees':all_consignees})
    
def history_PO(request):
    all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
    return render(request, 'inventoryapp/history_po.html', {'purchase_orders':all_purchase_orders})

def history_PRO(request):
    all_requisition_orders = Product_Requisition_Order.objects.all().order_by('Creation_Date')
    return render(request, 'inventoryapp/history_pro.html', {'requisition_orders':all_requisition_orders})

def categories_consignee_tags(request):
    consignees = Consignee.objects.all()
    categories = Category.objects.all()

    # Render the template with the consignees and categories
    return render(request, 'inventoryapp/categories_consignee_tags.html', {'consignees': consignees, 'categories': categories})

def add_category(request):
    if request.method == 'POST':
        Category_Name = request.POST.get('category_name')
        Category_Hex_Color_ID = request.POST.get('category_hex_color_id')
        Description = request.POST.get('description')
        Category_Product_Low_Stock_Threshold = request.POST.get('category_product_low_stock_threshold')
        Notes = request.POST.get('notes')

        existing_category = Category.objects.filter(Category_Name=Category_Name)
        if existing_category.exists():
            error_msg = 'Category Already Exists'
            return render(request, 'inventoryapp/categories_consignee_tags.html', {'error_msg': error_msg})
        else:
            Category.objects.create(
                Category_Name=Category_Name,
                Category_Hex_Color_ID=Category_Hex_Color_ID,
                Description=Description,
                Category_Product_Low_Stock_Threshold=Category_Product_Low_Stock_Threshold,
                Notes=Notes
            )
            return redirect('categories_consignee_tags')
    else:
        return render(request, 'inventoryapp/add_category.html')
    
def view_category(request, category_id):
    try:
        category = Category.objects.get(Category_ID=category_id)
        response_data = {
            'category_id': category.Category_ID,
            'name': category.Category_Name,
            'hex_color_id': category.Category_Hex_Color_ID,
            'description': category.Description,
            'low_stock_threshold': category.Category_Product_Low_Stock_Threshold,
            'notes': category.Notes,
        }
        return JsonResponse(response_data)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    
def view_category_details(request, category_id):
    try:
        category = Category.objects.get(pk=category_id)
        category_details = {
            'Category_Name': category.Category_Name,
            'Category_ID': category.Category_ID,
            'Category_Hex_Color_ID': category.Category_Hex_Color_ID,
            'Description': category.Description,
            'Category_Product_Low_Stock_Threshold': category.Category_Product_Low_Stock_Threshold,
            'Notes': category.Notes,
        }
        # Return the category details as JSON response
        return JsonResponse(category_details)
    except Category.DoesNotExist:
        # If the category doesn't exist, return a JSON response with an error message
        return JsonResponse({'error': 'Category does not exist'}, status=404)
    
def view_consignee_tag_details(request, consignee_id):
    try:
        consignee = get_object_or_404(Consignee, pk=consignee_id)
        consignee_details = {
            'Consignee_ID': consignee.Consignee_ID,
            'Consignee_Name': consignee.Consignee_Name,
            'Address_Line_1': consignee.Address_Line_1,
            'Barangay': consignee.Barangay,
            'Municipality': consignee.Municipality,
            'Province': consignee.Province,
            'Zip_Code': consignee.Zip_Code,
            'Primary_Contact_Number': consignee.Primary_Contact_Number,
            'Customer_Type': consignee.Customer_Type,
            'Notes': consignee.Notes,
            'Consignment_Period_Start': consignee.Consignment_Period_Start,
            'Consignment_Period_End': consignee.Consignment_Period_End,
            'Emergency_Contact_Number': consignee.Emergency_Contact_Number,
            'Email_Address': consignee.Email_Address,
            'Tag_Hex_Color_ID': consignee.Tag_Hex_Color_ID,
        }
        return JsonResponse(consignee_details)
    except Consignee.DoesNotExist:
        return JsonResponse({'error': 'Consignee does not exist'}, status=404)
    
def update_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    
    if request.method == 'POST':
        Category_Name = request.POST.get('category_name')
        Category_Hex_Color_ID = request.POST.get('category_hex_color_id')
        Description = request.POST.get('description')
        Category_Product_Low_Stock_Threshold = request.POST.get('category_product_low_stock_threshold')
        Notes = request.POST.get('notes')

        # Check if a category with the same name already exists excluding the current one
        existing_category = Category.objects.filter(Category_Name=Category_Name).exclude(pk=category_id)
        if existing_category.exists():
            error_msg = 'Category Already Exists'
            return render(request, 'inventoryapp/update_category.html', {'error_msg': error_msg, 'category': category})
        else:
            # Update the category fields
            category.Category_Name = Category_Name
            category.Category_Hex_Color_ID = Category_Hex_Color_ID
            category.Description = Description
            category.Category_Product_Low_Stock_Threshold = Category_Product_Low_Stock_Threshold
            category.Notes = Notes
            category.save()
            return redirect('categories_consignee_tags')
    else:
        return render(request, 'inventoryapp/update_category.html', {'category': category, 'category_id': category_id})