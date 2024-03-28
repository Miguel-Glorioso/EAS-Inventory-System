from django.shortcuts import render, redirect, get_object_or_404
from . models import Product, Category, Account, Consignee, Consignee_Product, Purchase_Order, Product_Ordered, Customer, Product_Requisition_Order, Stock_Ordered
from django.http import  JsonResponse
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils import timezone
from django.http import HttpResponse
from itertools import chain
from operator import attrgetter
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
    
    category_param = request.GET.get('category')
    consignee_param = request.GET.get('consignee')

    # Filter products by category if category parameter is provided
    if category_param:
         
        category = get_object_or_404(Category, Category_ID=category_param)
        all_inventory = all_inventory.filter(Category=category)

    # Filter products by consignee if consignee parameter is provided
    if consignee_param:
        print(consignee_param)  
        consignee = get_object_or_404(Consignee, Consignee_ID=consignee_param)
        consignee_products = all_consignee_products.filter(Consignee_ID=consignee)
        product_ids = consignee_products.values_list('Product_ID', flat=True)
        all_inventory = all_inventory.filter(Product_ID__in=product_ids)
    return render(request, 'inventoryapp/current_inventory.html', {'products':all_inventory, 'categories':all_categories, 'consignees':all_consignees, 'consignee_products':all_consignee_products})


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
        
        
        return redirect('current_inventory')
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
        Name = request.POST.get('customer_name')
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
        Notes = request.POST.get('c_notes')
        #Products = request.POST.getlist('sampleproduct') This should contain the list of product ids in the PO and quantity split by -
        #product and quantity can also be shown in a diff way this is just the first one i thought of
        PO_customer = None
        PO_consignee = None

        #Checks customer type
        print(Customer_Type)
        if Customer_Type == "Consignee":
            print('Ctypecheck: CON')
            existing_consignee = Consignee.objects.filter(
                Consignee_Name = Name,
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
                    Consignee_Name = Name,
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
                Customer_Name = Name,
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
                    Customer_Name = Name,
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
        current_date = timezone.now()
        PO = Purchase_Order.objects.create(
                Requested_Date=Requested_Date,
                Creation_Date = current_date,
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

def add_po_second(request):
    products = Product.objects.all()
    return render(request, 'inventoryapp/add_po_second.html', {'products': products})

def view_po(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
    return render(request, 'inventoryapp/view_po.html', {'po':purchase_order, 'products':products_ordered})

def close_po(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    if purchase_order.PO_Status != 'Closed':
        products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)

        for product in products_ordered:
            product_listing = Product.objects.get(Product_ID=product.Product_ID.Product_ID)
            product_listing.Actual_Inventory_Count -= product.Quantity
            product_listing.Reserved_Inventory_Count -= product.Quantity
            product_listing.save()

        purchase_order.Fulfilled_Date = timezone.now()
        purchase_order.PO_Status = 'Closed'
        purchase_order.Progress = 'Shipped'
        purchase_order.save()
    
    return redirect('current_pos')

def requisition_order_list(request):
    all_requisition_orders = Product_Requisition_Order.objects.all()
    return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders})


def add_requisition_order(request):
    if request.method == 'POST':
        Estimated_Receiving_Date = request.POST.get('estimated_receiving_date')
        PRO_Manufacturer = request.POST.get('manufacturer_name')
        Total_Cost =  request.POST.get('total_cost')
        PRO_Notes = request.POST.get('pro_notes')
        
        current_date = timezone.now()
        
        Product_Requisition_Order.objects.create(
            Estimated_Receiving_Date = Estimated_Receiving_Date,
            Creation_Date = current_date,
            PRO_Manufacturer = PRO_Manufacturer,
            Total_Cost = Total_Cost,
            Notes = PRO_Notes,
        )
        return redirect('current_pros')
    else:
        return render(request, 'inventoryapp/add_pro.html')
    
def view_pro(request, pk):
    product_requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    print(product_requisition_order, 'yes')
    stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID = pk)
    print(stocks_ordered)
    return render(request, 'inventoryapp/view_pro.html', {'pro':product_requisition_order, 'stocks':stocks_ordered})

def customer_list(request):
    all_direct = Customer.objects.all()
    all_consignees = Consignee.objects.all()
    all_customers = chain(all_direct, all_consignees)
    return render(request, 'inventoryapp/current_customers.html', {'customers':all_customers, 'consignees':all_consignees})

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
            return render(request, 'inventoryapp/create_consignee.html',  {'error_msg': error_msg})

        # If consignee doesn't exist, create a new one
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
            return redirect('current_customers')

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
        print(response_data)
        return JsonResponse(response_data)
    
    except (Customer.DoesNotExist, Consignee.DoesNotExist):
        return JsonResponse({'error': 'Customer not found'}, status=404)
    
def update_direct_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    error_msg = None

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
        return render(request, 'inventoryapp/update_direct_customer.html', {'customer': customer, 'error_msg': error_msg})