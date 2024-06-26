from django.shortcuts import render, redirect, get_object_or_404
from . models import Product, Category,  User, Account, Consignee, Consignee_Product, Purchase_Order, Product_Ordered, Customer, Product_Requisition_Order, Stock_Ordered, Partially_Fulfilled_History, Count_Edit_History
from django.http import  JsonResponse, FileResponse, HttpResponseForbidden
import json
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils import timezone
from datetime import datetime
from itertools import chain
from django.contrib.auth import authenticate, login, logout
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from django.contrib.auth.decorators import login_required,  user_passes_test
from django.contrib.auth.hashers import check_password
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Sum
import math
from django.templatetags.static import static

# Create your views here.

def account_login(request):
    if request.method == 'POST':
        login_username = request.POST.get('user_name')
        login_password = request.POST.get('password')
        user = authenticate(request, username=login_username, password=login_password)
        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            return redirect('current_inventory')
        else:
            error_msg = "Invalid Username/Password"
            return render(request, 'inventoryapp/login.html', {'error_msg': error_msg})
    else:
        return render(request, 'inventoryapp/login.html')
    
def account_logout(request):
    logout(request)

    return redirect('account_login')

@login_required 
def inventory_list(request):
    all_inventory = Product.objects.all()
    all_consignee_products = Consignee_Product.objects.all()
    all_categories = Category.objects.all()
    all_consignees = Consignee.objects.all()
    show_hidden = False
    
    category_param = request.GET.get('category')
    consignee_param = request.GET.get('consignee')
    stock_status_param = request.GET.get('stock_status')
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
        
    if stock_status_param:
        if stock_status_param == 'low_stock':
            all_inventory = all_inventory.filter(Product_Stock_Status='Low Stock')
        elif stock_status_param == 'no_stock':
            all_inventory = all_inventory.filter(Product_Stock_Status='No Stock')
        elif stock_status_param == 'regular_stock':
            all_inventory = all_inventory.filter(Product_Stock_Status='Regular Stock')
            

    # Count products with different stock statuses
    low_stock_count = all_inventory.filter(Product_Stock_Status='Low Stock').count()
    no_stock_count = all_inventory.filter(Product_Stock_Status='No Stock').count()
    regular_stock_count = all_inventory.filter(Product_Stock_Status='Regular Stock').count()
    total_products_count = all_inventory.count()

    return render(request, 'inventoryapp/current_inventory.html', {
        'products': all_inventory,
        'categories': all_categories,
        'consignees': all_consignees,
        'consignee_products': all_consignee_products,
        'show_hidden': show_hidden,
        'low_stock_count': low_stock_count,
        'no_stock_count': no_stock_count,
        'regular_stock_count': regular_stock_count,
        'total_products_count': total_products_count,
    })

@login_required 
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

        if Product_Initial_Count == None:
            Product_Initial_Count = 0

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
            messages.success(request, "Product added successfully.")
            return redirect('current_inventory')
    else:
        return render(request, 'inventoryapp/add_product.html',  {'categories': categories, 'consignees': consignees})

@login_required 
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
            'reserved_count': product.Reserved_Inventory_Count,  # Added this line at May 1
            'to_be_received_count': product.To_Be_Received_Inventory_Count,  # Added this line at May 1
            'category': product.Category.Category_Name,
            'tags': [consignee_product.Consignee_ID.Consignee_Name for consignee_product in con_p], 
            'threshold': product.Product_Low_Stock_Threshold,
            'picture': product.Picture.url if product.Picture else None,
        }
        return JsonResponse(response_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@login_required 
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
        
        messages.success(request, "Product updated successfully.")
        return redirect('current_inventory')
    else:
        return render(request, 'inventoryapp/update_product.html', {'p':p, 'con_p':con_p, 'con_p_ids':con_p_ids, 'categories': categories,  'consignees': consignees})

@login_required 
def purchase_order_list(request):
    all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')

    customer_type_param = request.GET.get('customer_type')
    progress_type_param = request.GET.get('progress_type')

    if customer_type_param:
        if customer_type_param == 'Direct':
            all_purchase_orders = all_purchase_orders.exclude(Consignee_ID__isnull=True)
        elif customer_type_param == 'Consignee':
            all_purchase_orders = all_purchase_orders.exclude(Customer_ID__isnull=True)
    if progress_type_param:
            if progress_type_param == 'Pending':
                all_purchase_orders = all_purchase_orders.filter(Progress='Pending')
            elif progress_type_param == 'Ongoing':
                all_purchase_orders = all_purchase_orders.filter(Progress='Ongoing')
            elif progress_type_param == 'Shipped':
                all_purchase_orders = all_purchase_orders.filter(Progress='Shipped')

    return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders})

@login_required 
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

@login_required 
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
        
        messages.success(request, "Purchase order added successfully.")
        return redirect('current_pos')
    
    else:
        return render(request, 'inventoryapp/add_po_consignee.html', {'products': all_products, 'consignees':all_consignees})

@login_required 
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
        
        PO_account = get_object_or_404(Account,pk=PO_account)
        
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
        
        messages.success(request, "Purchase order added successfully.")
        return redirect('current_pos')
    else:

        return render(request, 'inventoryapp/add_po_direct_customer.html', {'products': products})


# def add_po_second(request):
#     products = Product.objects.all()
#     return render(request, 'inventoryapp/add_po_second.html', {'products': products})

@login_required 
def view_po(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
    return render(request, 'inventoryapp/view_po.html', {'po':purchase_order, 'products':products_ordered})

@login_required 
def close_po(request, pk, account_id):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if request.method == 'POST':
        if purchase_order.PO_Status == 'Unfulfilled':
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

                    product_listing.save()

                purchase_order.Fulfilled_Date = timezone.now()
                purchase_order.PO_Status = 'Closed'
                purchase_order.Progress = 'Shipped'
                purchase_order.Account_ID_Closed_by = account
                purchase_order.save()
            
            else:
                error_msg = 'Insufficient Stock for Purchase Order'
                all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
                return render(request, 'inventoryapp/current_pos.html', {'error_msg':error_msg, 'purchase_orders':all_purchase_orders})
        
            messages.success(request, "Purchase order closed successfully.")
            return redirect('current_pos')
        else:
            error_msg = "This purchase order cannot be closed."
            all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
            return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders, 'error_msg':error_msg})
    else:
        all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
        return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders})
    
@login_required
def cancel_po(request, pk, account_id):

    if not request.user.is_superuser:
        error_msg = "You are not authorized to cancel purchase orders."
        all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
        return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders, 'error_msg':error_msg})
    
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if request.method == 'POST':
        if purchase_order.PO_Status == 'Unfulfilled':
            products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)

            for product in products_ordered:
                product_listing = Product.objects.get(Product_ID=product.Product_ID.Product_ID) #this is the actual product not the product ordered
                product_listing.Reserved_Inventory_Count -= product.Quantity #product reserved invetory count gets deducted
                product_listing.save()

            purchase_order.Fulfilled_Date = timezone.now()
            purchase_order.PO_Status = 'Cancelled'
            purchase_order.Progress = 'Cancelled'
            purchase_order.Account_ID_Closed_by = account
            purchase_order.save()

            messages.success(request, "Purchase order cancelled successfully.")
            return redirect('current_pos')
        else:
            error_msg = "This purchase order cannot be closed."
            all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
            return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders, 'error_msg':error_msg})
        
    else:
        all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
        return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders})
    
@login_required
def cancel_po_specific(request, pk, account_id):

    if not request.user.is_superuser:
        error_msg = "You are not authorized to cancel purchase orders."
        purchase_order = get_object_or_404(Purchase_Order, pk=pk)
        products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
        return render(request, 'inventoryapp/view_po.html', {'po':purchase_order, 'products':products_ordered, 'error_msg':error_msg})
    
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if request.method == 'POST':
        if purchase_order.PO_Status == 'Unfulfilled':
            products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)

            for product in products_ordered:
                product_listing = Product.objects.get(Product_ID=product.Product_ID.Product_ID) #this is the actual product not the product ordered
                product_listing.Reserved_Inventory_Count -= product.Quantity #product reserved invetory count gets deducted
                product_listing.save()

            purchase_order.Fulfilled_Date = timezone.now()
            purchase_order.PO_Status = 'Cancelled'
            purchase_order.Progress = 'Cancelled'
            purchase_order.Account_ID_Closed_by = account
            purchase_order.save()

            messages.success(request, "Purchase order cancelled successfully.")
            return redirect('current_pos')
        else:
            error_msg = "You are not authorized to cancel purchase orders."
            purchase_order = get_object_or_404(Purchase_Order, pk=pk)
            products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
            return render(request, 'inventoryapp/view_po.html', {'po':purchase_order, 'products':products_ordered, 'error_msg':error_msg})
        
    else:
        all_purchase_orders = Purchase_Order.objects.all().order_by('Requested_Date')
        return render(request, 'inventoryapp/current_pos.html', {'purchase_orders':all_purchase_orders})

@login_required 
def requisition_order_list(request):
    all_requisition_orders = Product_Requisition_Order.objects.all()

    progress_type_param = request.GET.get('progress_type')

    if progress_type_param:
            if progress_type_param == 'Pending':
                all_requisition_orders = all_requisition_orders.filter(Progress='Pending')
            elif progress_type_param == 'To be Picked Up':
                all_requisition_orders = all_requisition_orders.filter(Progress='To be Picked Up')

    return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders})

@login_required 
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

@login_required 
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

        messages.success(request, "Product requisition order added successfully.")
        return redirect('current_pros')
    else:
        return render(request, 'inventoryapp/add_pro.html', {'products': products})

@login_required 
def update_pro(request, pk):
    PRO = get_object_or_404(Product_Requisition_Order, pk=pk)
    all_inventory = Product.objects.all()
    stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=PRO)

    if request.method == 'POST':
        estimated_receiving_date = request.POST.get('estimated_receiving_date')
        manufacturer_name = request.POST.get('manufacturer_name')
        total_cost =  request.POST.get('total_cost')
        pro_notes = request.POST.get('pro_notes')
        Products = request.POST.get('all_products')

        
        PRO.Estimated_Receiving_Date=estimated_receiving_date
        PRO.PRO_Manufacturer=manufacturer_name
        PRO.Total_Cost=total_cost
        PRO.Notes = pro_notes

        Products = Products[:-1]
        Ordered_Products= Products.split("-")
        new_stocks_ordered = []
        print(Ordered_Products, 'dshjd')
        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            ordered_products = stocks_ordered.filter(Product_ID=values[0])

            if ordered_products.exists():
                ordered_product = ordered_products.first()
                quantity_diff = int(values[1]) - ordered_product.Quantity
                ordered_product.Quantity = values[1]
                product_object.To_Be_Received_Inventory_Count += quantity_diff
                ordered_product.save()
                product_object.save()
                new_stocks_ordered.append(ordered_product)
            else:
                product_object.To_Be_Received_Inventory_Count += int(values[1])
                product_object.save()
                new_product_ordered = Stock_Ordered.objects.create(Product_ID=product_object, Product_Requisition_ID=PRO, Quantity=values[1])
                new_stocks_ordered.append(new_product_ordered)

        # Create a list of Product_Ordered objects to delete
        products_to_delete = [s_o for s_o in stocks_ordered if s_o not in new_stocks_ordered]

        # Delete the Product_Ordered objects
        for s_o in products_to_delete:
            product_object = Product.objects.get(Product_ID=s_o.Product_ID.Product_ID)
            product_object.To_Be_Received_Inventory_Count -= s_o.Quantity
            product_object.save()
            s_o.delete()

        messages.success(request, "Product requisition order updated successfully.")
        return redirect('current_pros')
    else:
        
        return render(request, 'inventoryapp/update_pro.html', {'requisition_order': PRO, 'products': all_inventory, 'stock_ordered_items': stocks_ordered})

@login_required     
def view_pro(request, pk):
    product_requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)
    
    previous_parfills_combined = Partially_Fulfilled_History.objects.filter(Stock__in=stocks_ordered).values('Stock').annotate(total_quantity=Sum('Partially_Fulfilled_Quantity'))
    
    no_parfills = {}

    has_parfills = bool(previous_parfills_combined)
    
    for stock in stocks_ordered:
        if stock.pk not in [item['Stock'] for item in previous_parfills_combined]:
            no_parfills[stock.pk] = stock 
    print(previous_parfills_combined, 'ched', has_parfills)
    return render(request, 'inventoryapp/view_pro.html', {'pro': product_requisition_order, 'stocks': stocks_ordered, 'previous_parfills': previous_parfills_combined, 'no_parfills': no_parfills, 'has_parfills':has_parfills})

@login_required 
def close_pro(request, pk, account_id):
    requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if request.method == 'POST':
        if requisition_order.PRO_Status == 'Ongoing':
            stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)

            for stock in stocks_ordered:
                stock_listing = Product.objects.get(Product_ID=stock.Product_ID.Product_ID) #this is the actual product not the product ordered
                parfills = Partially_Fulfilled_History.objects.filter(Stock=stock)
                total_parfill_quantity = sum(parfill.Partially_Fulfilled_Quantity for parfill in parfills)
                total_quantity = stock.Quantity - total_parfill_quantity
                stock_listing.Actual_Inventory_Count += total_quantity #product inventory count gets deducted
                stock_listing.To_Be_Received_Inventory_Count -= total_quantity #product reserved invetory count gets deducted

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
        
            messages.success(request, "Product requisition order closed successfully.")
            return redirect('current_pros')
        else:
            error_msg = "This purchase order cannot be closed."
            all_requisition_orders = Product_Requisition_Order.objects.all()
            return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders, 'error_msg':error_msg})
        
            
    else:
        all_requisition_orders = Product_Requisition_Order.objects.all()
        return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders})
    

@login_required 
def cancel_pro(request, pk, account_id):
    if not request.user.is_superuser:
        error_msg = "You are not authorized to cancel product requisition orders."
        all_requisition_orders = Product_Requisition_Order.objects.all()
        return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders, 'error_msg':error_msg})

    requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if request.method == 'POST':
        if requisition_order.PRO_Status == 'Ongoing':
            stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)

            for stock in stocks_ordered:
                parfill = Partially_Fulfilled_History.objects.filter(Stock=stock)
                if parfill:
                    error_msg = "Cannot cancel product requisition order that is partially fulfilled"
                    all_requisition_orders = Product_Requisition_Order.objects.all()
                    return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders, 'error_msg':error_msg})

            for stock in stocks_ordered:
                stock_listing = Product.objects.get(Product_ID=stock.Product_ID.Product_ID) #this is the actual product not the product ordered
                stock_listing.To_Be_Received_Inventory_Count -= stock.Quantity #product reserved invetory count gets deducte
                stock_listing.save()

            requisition_order.Received_Date = timezone.now()
            requisition_order.PRO_Status = 'Cancelled'
            requisition_order.Progress = 'Cancelled'
            requisition_order.Account_ID_Closed_by = account
            requisition_order.save()
        
            messages.success(request, "Product requisition order cancelled successfully.")
            return redirect('current_pros')
        else:
            error_msg = "This product requisition order cannot be cancelled."
            all_requisition_orders = Product_Requisition_Order.objects.all()
            return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders, 'error_msg':error_msg})
        
    else:
        all_requisition_orders = Product_Requisition_Order.objects.all()
        return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders})

@login_required 
def cancel_pro_specific(request, pk, account_id):
    if not request.user.is_superuser:
        product_requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
        stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)
        
        previous_parfills_combined = Partially_Fulfilled_History.objects.filter(Stock__in=stocks_ordered).values('Stock').annotate(total_quantity=Sum('Partially_Fulfilled_Quantity'))
        
        no_parfills = {}
        has_parfills = bool(previous_parfills_combined)
        for stock in stocks_ordered:
            if stock.pk not in [item['Stock'] for item in previous_parfills_combined]:
                no_parfills[stock.pk] = stock 
        
        error_msg = "You are not authorized to cancel product requisition orders."
        return render(request, 'inventoryapp/view_pro.html', {'pro': product_requisition_order, 'stocks': stocks_ordered, 'previous_parfills': previous_parfills_combined, 'no_parfills': no_parfills, 'has_parfills':has_parfills, 'error_msg':error_msg})
    
    requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    account = get_object_or_404(Account,pk=account_id )
    if request.method == 'POST':
        if requisition_order.PRO_Status == 'Ongoing':
            stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)

            for stock in stocks_ordered:
                stock_listing = Product.objects.get(Product_ID=stock.Product_ID.Product_ID) #this is the actual product not the product ordered
                stock_listing.To_Be_Received_Inventory_Count -= stock.Quantity #product reserved invetory count gets deducte
                stock_listing.save()

            requisition_order.Received_Date = timezone.now()
            requisition_order.PRO_Status = 'Cancelled'
            requisition_order.Progress = 'Cancelled'
            requisition_order.Account_ID_Closed_by = account
            requisition_order.save()
            
            messages.success(request, "Product requisition order cancelled successfully.")
            return redirect('current_pros')
        else:
            product_requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
            stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)
            
            previous_parfills_combined = Partially_Fulfilled_History.objects.filter(Stock__in=stocks_ordered).values('Stock').annotate(total_quantity=Sum('Partially_Fulfilled_Quantity'))
            
            no_parfills = {}
            
            for stock in stocks_ordered:
                if stock.pk not in [item['Stock'] for item in previous_parfills_combined]:
                    no_parfills[stock.pk] = stock 
            
            error_msg = "This purchase order cannot be cancelled."
            return render(request, 'inventoryapp/view_pro.html', {'pro': product_requisition_order, 'stocks': stocks_ordered, 'previous_parfills': previous_parfills_combined, 'no_parfills': no_parfills, 'error_msg':error_msg})
        
    else:
        all_requisition_orders = Product_Requisition_Order.objects.all()
        return render(request, 'inventoryapp/current_pros.html', {'requisition_orders':all_requisition_orders})

@login_required 
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
            
    return render(request, 'inventoryapp/current_customers.html', {'customers':all_customers })

@login_required 
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
            messages.success(request, "Direct customer added successfully.")
            return redirect('current_customers')
    else:
        return render(request, 'inventoryapp/create_direct_customer.html')

@login_required 
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
        if existing_consignee.exists():
            error_msg = 'Consignee Already Exists'
            return render(request, 'inventoryapp/create_consignee.html',  {'error_msg': error_msg})
        
        existing_color = Consignee.objects.filter(Tag_Hex_Color_ID=Tag_Hex_Color_ID)

        if existing_color.exists():
            error_msg = 'Consignee Color Already Exists'
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
            messages.success(request, "Consignee added successfully.")
            return redirect('current_customers')

    else:
        return render(request, 'inventoryapp/create_consignee.html')

@login_required     
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
        print(Tag_Hex_Color_ID)
        # Check if the consignee already exists
        existing_consignee = Consignee.objects.filter(
            Consignee_Tag_ID=Consignee_Tag_ID,
            Consignee_Name=Consignee_Name,
        )
        if existing_consignee.exists():
            error_msg = 'Consignee Already Exists'
            return render(request, 'inventoryapp/create__consignee.html',  {'error_msg': error_msg})
        
        existing_color = Consignee.objects.filter(Tag_Hex_Color_ID=Tag_Hex_Color_ID)

        if existing_color.exists():
            error_msg = 'Consignee Color Already Exists'
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
            messages.success(request, "Consignee added successfully.")
            return redirect('categories_consignee_tags')

    else:
        return render(request, 'inventoryapp/create__consignee.html')

@login_required 
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
                'tagID': customer.Consignee_Tag_ID,
                'consignment_period_start': customer.Consignment_Period_Start,
                'consignment_period_end': customer.Consignment_Period_End,
                'emergency_contact_number': customer.Emergency_Contact_Number,
                'email_address': customer.Email_Address,
                'tag_hex_color_id': customer.Tag_Hex_Color_ID,
            })
        return JsonResponse(response_data)
    
    except (Customer.DoesNotExist, Consignee.DoesNotExist):
        return JsonResponse({'error': 'Customer not found'}, status=404)

@login_required     
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

        messages.success(request, "Direct customer updated successfully.")
        return redirect('current_customers')
    else:
        return render(request, 'inventoryapp/update_direct_customer.html', {'customer': customer})

@login_required     
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

        # Check if the consignee already exists
        existing_consignee = Consignee.objects.filter(
            Consignee_Tag_ID=Consignee_Tag_ID,
            Consignee_Name=Consignee_Name,
        ).exclude(pk=pk)

        if existing_consignee.exists():
            error_msg = 'Consignee Already Exists'
            return render(request, 'inventoryapp/update_consignee.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string, 'error_msg': error_msg})
        
        existing_color = Consignee.objects.filter(Tag_Hex_Color_ID=Tag_Hex_Color_ID).exclude(pk=pk)

        if existing_color.exists():
            error_msg = 'Consignee Color Already Exists'
            return render(request, 'inventoryapp/update_consignee.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string, 'error_msg': error_msg})

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
        consignee.Tag_Hex_Color_ID = Tag_Hex_Color_ID

        consignee.save()

        messages.success(request, "Consignee updated successfully.")
        return redirect('current_customers')

    else:
        return render(request, 'inventoryapp/update_consignee.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string})

@login_required 
def update_PO_direct_customer(request, po_pk, c_pk):
    PO = get_object_or_404(Purchase_Order, pk=po_pk)
    C = get_object_or_404(Customer, pk=c_pk)
    products_ordered =  Product_Ordered.objects.filter(Purchase_Order_ID=po_pk)
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
        
        PO.Requested_Date = Requested_Date
        PO.Shipping_Method = Shipping_Method
        PO.Order_Method = Order_Method
        PO.Total_Due = Total_Price
        PO.Notes = Order_Notes
        PO.save()

        C.Customer_Name = Customer_Name
        C.Primary_Contact_Number = Primary_Contact
        C.Address_Line_1 = Address_Line1
        C.Province = Province
        C.Municipality = Municipality
        C.Barangay = Barangay
        C.Zip_Code = Zip_Code
        C.Notes = Customer_Notes
        C.save()

        Products = Products[:-1]
        Ordered_Products= Products.split("-")
        new_products_ordered = []

        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            ordered_products = products_ordered.filter(Product_ID=values[0])

            if ordered_products.exists():
                ordered_product = ordered_products.first()
                quantity_diff = int(values[1]) - ordered_product.Quantity
                ordered_product.Quantity = values[1]
                product_object.Reserved_Inventory_Count += quantity_diff
                ordered_product.save()
                product_object.save()
                new_products_ordered.append(ordered_product)
            else:
                product_object.Reserved_Inventory_Count += int(values[1])
                product_object.save()
                new_product_ordered = Product_Ordered.objects.create(Product_ID=product_object, Purchase_Order_ID=PO, Quantity=values[1])
                new_products_ordered.append(new_product_ordered)

        # Create a list of Product_Ordered objects to delete
        products_to_delete = [p_o for p_o in products_ordered if p_o not in new_products_ordered]

        # Delete the Product_Ordered objects
        for p_o in products_to_delete:
            product_object = Product.objects.get(Product_ID=p_o.Product_ID.Product_ID)
            product_object.Reserved_Inventory_Count -= p_o.Quantity
            product_object.save()
            p_o.delete()
        
        messages.success(request, "Purchase order updated successfully.")
        return redirect('current_pos')
        
    else:
        return render(request, 'inventoryapp/update_po_direct_customer.html', {'PO':PO, 'C':C, 'products_ordered':products_ordered, 'products':products})

@login_required 
def update_PO_consignee(request, po_pk, c_pk):
    PO = get_object_or_404(Purchase_Order, pk=po_pk)
    C = get_object_or_404(Consignee, pk=c_pk)
    all_consignees = Consignee.objects.all()
    products_ordered =  Product_Ordered.objects.filter(Purchase_Order_ID=po_pk)
    products = Product.objects.all() 
    if request.method == 'POST':
        Requested_Date = request.POST.get('requested_date')
        Order_Notes = request.POST.get('order_notes')
        Products = request.POST.get('all_products')
        Total_Price = request.POST.get('total_price')
        Shipping_Method = request.POST.get('shipping_method')
        Order_Method = request.POST.get('order_method')
        PO_Consignee = request.POST.get('consignee')

        PO_Consignee = get_object_or_404(Consignee, Consignee_ID=PO_Consignee)

        PO.Requested_Date = Requested_Date
        PO.Consignee_ID=PO_Consignee
        PO.Shipping_Method = Shipping_Method
        PO.Order_Method = Order_Method
        PO.Total_Due = Total_Price
        PO.Notes = Order_Notes
        PO.save()

        Products = Products[:-1]
        Ordered_Products= Products.split("-")
        new_products_ordered = []

        for op in Ordered_Products:
            values = op.split(":")
            product_object = Product.objects.get(Product_ID=values[0])

            ordered_products = products_ordered.filter(Product_ID=values[0])

            if ordered_products.exists():
                ordered_product = ordered_products.first()
                quantity_diff = int(values[1]) - ordered_product.Quantity
                ordered_product.Quantity = values[1]
                product_object.Reserved_Inventory_Count += quantity_diff
                ordered_product.save()
                product_object.save()
                new_products_ordered.append(ordered_product)
            else:
                product_object.Reserved_Inventory_Count += int(values[1])
                product_object.save()
                new_product_ordered = Product_Ordered.objects.create(Product_ID=product_object, Purchase_Order_ID=PO, Quantity=values[1])
                new_products_ordered.append(new_product_ordered)

        # Create a list of Product_Ordered objects to delete
        products_to_delete = [p_o for p_o in products_ordered if p_o not in new_products_ordered]

        # Delete the Product_Ordered objects
        for p_o in products_to_delete:
            product_object = Product.objects.get(Product_ID=p_o.Product_ID.Product_ID)
            product_object.Reserved_Inventory_Count -= p_o.Quantity
            product_object.save()
            p_o.delete()

        messages.success(request, "Purchase order updated successfully.")
        return redirect('current_pos')
    else:
        return render(request, 'inventoryapp/update_po_consignee.html', {'PO':PO, 'C':C, 'products_ordered':products_ordered, 'products':products, 'consignees':all_consignees})

@login_required     
def history_PO(request):
    all_purchase_orders = Purchase_Order.objects.all().order_by('Fulfilled_Date')
    return render(request, 'inventoryapp/history_po.html', {'purchase_orders':all_purchase_orders})

def view_po_history(request, pk):
    purchase_order = get_object_or_404(Purchase_Order, pk=pk)
    products_ordered = Product_Ordered.objects.filter(Purchase_Order_ID=pk)
    return render(request, 'inventoryapp/view_po_history.html', {'po':purchase_order, 'products':products_ordered})


@login_required 
def history_PRO(request):
    all_requisition_orders = Product_Requisition_Order.objects.all().order_by('Creation_Date')
    return render(request, 'inventoryapp/history_pro.html', {'requisition_orders':all_requisition_orders})

def view_pro_history(request, pk):
    requisition_order = get_object_or_404(Product_Requisition_Order, pk=pk)
    stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=pk)
    return render(request, 'inventoryapp/view_pro_history.html', {'pro':requisition_order, 'stocks':stocks_ordered})

@login_required 
def categories_consignee_tags(request):
    consignees = Consignee.objects.all()
    categories = Category.objects.all()

    # Render the template with the consignees and categories
    return render(request, 'inventoryapp/categories_consignee_tags.html', {'consignees': consignees, 'categories': categories})

@login_required 
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
            return render(request, 'inventoryapp/add_category.html', {'error_msg': error_msg})
        
        existing_color = Category.objects.filter(Category_Hex_Color_ID=Category_Hex_Color_ID)

        if existing_color.exists():
            error_msg = 'Category Color Already Exists'
            return render(request, 'inventoryapp/add_category.html', {'error_msg': error_msg})
        
        else:
            Category.objects.create(
                Category_Name=Category_Name,
                Category_Hex_Color_ID=Category_Hex_Color_ID,
                Description=Description,
                Category_Product_Low_Stock_Threshold=Category_Product_Low_Stock_Threshold,
                Notes=Notes
            )
            messages.success(request, "Category added successfully.")
            return redirect('categories_consignee_tags')
    else:
        return render(request, 'inventoryapp/add_category.html')

@login_required     
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

@login_required 
def generate_inventory_summary_screen(request):
    all_inventory = Product.objects.all()
    all_consignee_products = Consignee_Product.objects.all()
    all_categories = Category.objects.all()
    all_consignees = Consignee.objects.all()
    return render(request, 'inventoryapp/generate_inventory_summary_screen.html',{'products':all_inventory, 'categories':all_categories, 'consignees':all_consignees, 'consignee_products':all_consignee_products})

@login_required 
def generate_inventory_summary(request):
    # Retrieve all products
    all_inventory = Product.objects.all()

    # Create a PDF buffer
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter, bottomup=1)

    # Set Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, "Inventory Summary")

    # Insert generated date, time, and page information
    generated_info = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {request.user}"
    # page_info = f"Page 1 out of {math.ceil(len(all_inventory) / 50) + 1}"  # Assuming 50 products per page
    c.drawString(100, 730, generated_info)
    # c.drawString(100, 710, page_info)

    # Draw a line for the separator
    c.line(0, 700, letter[0], 700)

    # Define table headers
    table_data = [
        ["Name", "ID", "Actual Count", "Reserved", "To Be Received", "Categories"]
    ]

    # Populate table data
    for product in all_inventory:
        table_data.append([
            product.Name,
            str(product.EAS_Product_ID),
            str(product.Actual_Inventory_Count),
            str(product.Reserved_Inventory_Count),
            str(product.To_Be_Received_Inventory_Count),
            str(product.Category),
        ])

    # Create the table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Center text vertically
    ]))

    # Calculate the width and height of the table
    table_width, table_height = table.wrap(inch, inch)

    # Calculate the position of the table on the page
    x = (letter[0] - table_width) / 2
    y = (letter[1] - table_height) / 2

    # Draw the table on the canvas
    table.drawOn(c, x, y)

    # Add header and footer
    footer = "Everything About Santa"
    c.setFont("Helvetica", 10)
    c.drawString(inch / 2, 0.5 * inch, footer)

    # Save the PDF
    c.showPage()
    c.save()
    buf.seek(0)

    # Return the PDF response
    return FileResponse(buf, as_attachment=True, filename="Summary Report.pdf")


@login_required 
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

@login_required     
def view_consignee_tag_details(request, consignee_id):
    try:
        consignee = get_object_or_404(Consignee, pk=consignee_id)
        consignee_details = {
            'Consignee_ID': consignee.Consignee_ID,
            'Consignee_Tag': consignee.Consignee_Tag_ID,
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

@login_required     
def update_category(request, pk):
    category = Category.objects.get(pk=pk)
    
    if request.method == 'POST':
        Category_Name = request.POST.get('category_name')
        Category_Hex_Color_ID = request.POST.get('category_hex_color_id')
        Description = request.POST.get('description')
        Category_Product_Low_Stock_Threshold = request.POST.get('category_product_low_stock_threshold')
        Notes = request.POST.get('notes')

        # Check if a category with the same name already exists excluding the current one
        existing_category = Category.objects.filter(Category_Name=Category_Name).exclude(pk=pk)

        if existing_category.exists():
            error_msg = 'Category Already Exists'
            return render(request, 'inventoryapp/update_category.html', {'category': category, 'error_msg':error_msg})
        
        existing_color = Category.objects.filter(Category_Hex_Color_ID=Category_Hex_Color_ID).exclude(pk=pk)

        if existing_color.exists():
            error_msg = 'Category Color Already Exists'
            return render(request, 'inventoryapp/update_category.html', {'category': category, 'error_msg':error_msg})
        
        else:
            # Update the category fields
            category.Category_Name = Category_Name
            category.Category_Hex_Color_ID = Category_Hex_Color_ID
            category.Description = Description
            category.Category_Product_Low_Stock_Threshold = Category_Product_Low_Stock_Threshold
            category.Notes = Notes
            category.save()
            messages.success(request, "Category updated successfully.")
            return redirect('categories_consignee_tags')
    else:
        return render(request, 'inventoryapp/update_category.html', {'category': category})

@login_required     
def update_tags(request, pk):
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

        # Check if the consignee already exists
        existing_consignee = Consignee.objects.filter(
            Consignee_Tag_ID=Consignee_Tag_ID,
            Consignee_Name=Consignee_Name,
        ).exclude(pk=pk)

        if existing_consignee.exists():
            error_msg = 'Consignee Already Exists'
            return render(request, 'inventoryapp/update_tags.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string, 'error_msg': error_msg})
        
        existing_color = Consignee.objects.filter(Tag_Hex_Color_ID=Tag_Hex_Color_ID).exclude(pk=pk)

        if existing_color.exists():
            error_msg = 'Consignee Color Already Exists'
            return render(request, 'inventoryapp/update_tags.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string, 'error_msg': error_msg})

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
        consignee.Tag_Hex_Color_ID = Tag_Hex_Color_ID

        consignee.save()

        messages.success(request, "Consignee updated successfully.")
        return redirect('categories_consignee_tags')

    else:
        return render(request, 'inventoryapp/update_tags.html', {'consignee': consignee, 'Start_date_string':Start_date_string, 'End_date_string':End_date_string})

@login_required 
def my_account(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        passcode_input = data.get('passcode')
        user = request.user
        if check_password(passcode_input, user.password):
            return JsonResponse({'valid': True})
        else:
            return JsonResponse({'valid': False})
    else:
        return render(request, 'inventoryapp/my_account.html')

@login_required 
def employee_accounts(request):
    if not request.user.is_superuser:
        previous_page = request.META.get('HTTP_REFERER', '/') 
        return redirect(previous_page)
    
    all_users = User.objects.filter(is_superuser=False)

    visible_users = User.objects.filter(is_superuser=False, account__Visibility=True)
    user_count = visible_users.count()
    show_hidden = False

    hidden_param = request.GET.get('showHidden')

    if hidden_param:
        show_hidden = True
        user_count = all_users.count()
        print("hide")
    print(all_users)

    return render(request, 'inventoryapp/employee_accounts.html', {'users': all_users, 'user_count':user_count, 'show_hidden':show_hidden})


@login_required 
def edit_my_account(request):
    if request.method == 'POST':
        user = request.user

        # Get the form data
        New_password = request.POST.get('new_password')
        Reenter_new_password = request.POST.get('reenter_new_password')
        New_username = request.POST.get('username')
        Profile_picture = request.FILES.get('profile_picture')
        Image_removed = request.POST.get('removed_profile_picture')

        if New_password == "no need password" and Reenter_new_password == "no need password":
            # Skip password update
            New_password = None
        else:
            # Check if passwords match
            if New_password != Reenter_new_password:
                error_msg = "Passwords do not match"
                return render(request, 'inventoryapp/edit_my_account.html', {'error_msg': error_msg})

        # Update password if it's provided
        if New_password:
            user.set_password(New_password)
        if New_username:
            user.username = New_username

        if Image_removed == 'removed':
            previous_picture_filename = user.account.Profile_Picture.name
            user.account.Profile_Picture = None
            user.account.save()
            
            if previous_picture_filename:
                default_storage.delete(previous_picture_filename)
        
        elif Profile_picture is not None:
            previous_picture_filename = user.account.Profile_Picture.name
            user.account.Profile_Picture = Profile_picture
            user.account.save()
            
            if previous_picture_filename:
                default_storage.delete(previous_picture_filename)
            
        user.save()
        logout(request)
        return redirect('account_login')

    return render(request, 'inventoryapp/edit_my_account.html')

@login_required 
def add_new_employee(request):
    if request.method == 'POST':
        First_name = request.POST.get("first_name")
        Last_name = request.POST.get("last_name")
        Username = request.POST.get("username")
        Password = request.POST.get("password")
        Profile_picture = request.FILES.get('profile_picture') 
        
        existing_user = User.objects.filter(
            username = Username
        )

        if existing_user:
            error_msg = 'Username Already Exists'
            return render(request, 'inventoryapp/add_new_employee.html',{'error_msg': error_msg})
        
        user = User.objects.create_user(username=Username, password=Password)
        
        Account.objects.create(
            user=user,
            Profile_Picture=Profile_picture,
            First_Name=First_name,
            Last_Name=Last_name,
            Role='Employee',
            Visibility=True
        )
        messages.success(request, "Employee account added successfully.")
        return redirect('employee_accounts')
    else:
        return render(request, 'inventoryapp/add_new_employee.html')

@login_required 
def view_employee(request, pk):
    Employee = get_object_or_404(Account, Account_ID=pk)
    return render(request, 'inventoryapp/view_employee.html', {"Employee":Employee})

@login_required 
def update_employee(request, pk):
    Employee = get_object_or_404(Account, Account_ID=pk)
    if request.method == 'POST':
        user = Employee.user
        
        New_password = request.POST.get('new_password')
        Reenter_new_password = request.POST.get('reenter_new_password')
        New_username = request.POST.get('username')
        Profile_picture = request.FILES.get('profile_picture')
        Image_removed = request.POST.get('removed_profile_picture')

        if New_password == "no need password" and Reenter_new_password == "no need password":
            # Skip password update
            New_password = None
        else:
            # Check if passwords match
            if New_password != Reenter_new_password:
                error_msg = "Passwords do not match"
                return render(request, 'inventoryapp/update_employee.html', {'error_msg': error_msg, "Employee": Employee})

        # Update password if it's provided
        if New_password:
            user.set_password(New_password)
        if New_username:
            user.username = New_username

        if Image_removed == 'removed':
            previous_picture_filename = user.account.Profile_Picture.name
            user.account.Profile_Picture = None
            user.account.save()
            
            if previous_picture_filename:
                default_storage.delete(previous_picture_filename)
        
        elif Profile_picture is not None:
            previous_picture_filename = user.account.Profile_Picture.name
            user.account.Profile_Picture = Profile_picture
            user.account.save()
            
            if previous_picture_filename:
                default_storage.delete(previous_picture_filename)
            
        user.save()
        messages.success(request, "Employee account updated successfully.")
        return redirect('employee_accounts')
    else:
        return render(request, 'inventoryapp/update_employee.html', {"Employee": Employee})


@login_required 
def hide_account(request, pk):
    if request.method == 'POST':
        # Perform account hiding logic
        employee = get_object_or_404(Account, Account_ID=pk)
        employee.Visibility = False
        employee.save()
        messages.success(request, "Employee account hid successfully.")
        return redirect('employee_accounts')
    else:
        return redirect('employee_accounts')

@login_required    
def unhide_account(request, pk):
      if request.method == 'POST':
          # Perform account unhiding logic
          employee = get_object_or_404(Account, Account_ID=pk)
          employee.Visibility = True
          employee.save()
          messages.success(request, "Employee account unhid successfully.")
          return redirect('employee_accounts')
      else:
          return redirect('employee_accounts')

@login_required 
def partially_fulfill(request, pk):
    PRO = get_object_or_404(Product_Requisition_Order, pk=pk)
    stocks_ordered = Stock_Ordered.objects.filter(Product_Requisition_ID=PRO)
    previous_parfills_combined = Partially_Fulfilled_History.objects.filter(Stock__in=stocks_ordered).values('Stock').annotate(total_quantity=Sum('Partially_Fulfilled_Quantity'))
    
    no_parfills = {}

    for stock in stocks_ordered:
        if stock.pk not in [item['Stock'] for item in previous_parfills_combined]:
            no_parfills[stock.pk] = stock 
    
    if request.method == 'POST':
        Parfill_account = request.POST.get('account')

        Parfill_account = get_object_or_404(Account,pk=Parfill_account)
        for key in request.POST.keys():
            if key.startswith('quantity_'):
                product_pk = key.split('_')[-1]
                quantity = request.POST[key]

                if int(quantity) > 0:
                    image = request.FILES.get(f'parfill_picture_{product_pk}')
                    text_report = request.POST.get(f'text_report_{product_pk}')
                    
                    product_object = Product.objects.get(Product_ID=product_pk)

                    product_object.Actual_Inventory_Count += int(quantity)
                    product_object.To_Be_Received_Inventory_Count -= int(quantity)
                    
                    if product_object.Product_Low_Stock_Threshold:
                        if int(product_object.Actual_Inventory_Count) <= int(product_object.Product_Low_Stock_Threshold):
                            product_object.Product_Stock_Status = 'Low Stock'
                        else:
                            product_object.Product_Stock_Status = 'Regular Stock'

                    else:
                        if int(product_object.Actual_Inventory_Count) <= int(product_object.Category.Category_Product_Low_Stock_Threshold):
                            product_object.Product_Stock_Status = 'Low Stock'
                        else:
                            product_object.Product_Stock_Status = 'Regular Stock'
                    product_object.save()
                    
                    current_date = timezone.now()

                    stock = Stock_Ordered.objects.get(Product_ID=product_object, Product_Requisition_ID=PRO)
                    Partially_Fulfilled_History.objects.create(
                        Date_Updated = current_date,
                        Partially_Fulfilled_Quantity = int(quantity),
                        Image_Report = image,
                        Text_Report = text_report,
                        Stock = stock,
                        Account_ID = Parfill_account
                    )
                else:
                    pass
        messages.success(request, "Product requisition order partially fulfilled")
        return redirect('current_pros')

    return render(request, 'inventoryapp/partially_fulfill.html', {'requisition_order': PRO, 'stock_ordered_items': stocks_ordered, 'previous_parfills':previous_parfills_combined, 'no_parfills':no_parfills})

@login_required 
def history_partially_fulfilled(request):
    partially_fulfilled_history = Partially_Fulfilled_History.objects.all()
    return render(request, 'inventoryapp/history_partially_fulfilled.html' , {'partially_fulfilled_history':partially_fulfilled_history})

@login_required 
def edit_count(request):
    products = Product.objects.all()
    if request.method == 'POST':
            cEdit_account = request.POST.get('account')

            cEdit_account = get_object_or_404(Account,pk=cEdit_account)
            for key in request.POST.keys():
                if key.startswith('updated_count_'):
                    product_pk = key.split('_')[-1]
                    updated_count = request.POST[key]
                    image_report= request.FILES.get(f'image_report_{product_pk}')
                    text_report = request.POST.get(f'text_report_{product_pk}')

                    product = Product.objects.get(Product_ID=product_pk)

                    initial_count = product.Actual_Inventory_Count

                    product.Actual_Inventory_Count = int(updated_count)

                    if product.Product_Low_Stock_Threshold:
                        if int(product.Actual_Inventory_Count) == 0:
                            product.Product_Stock_Status = 'No Stock'
                        elif int(product.Actual_Inventory_Count) <= int(product.Product_Low_Stock_Threshold):
                            product.Product_Stock_Status = 'Low Stock'
                        else:
                            product.Product_Stock_Status = 'Regular Stock'
                    else:
                        if int(product.Actual_Inventory_Count) == 0:
                            product.Product_Stock_Status = 'No Stock'
                        elif int(product.Actual_Inventory_Count) <= int(product.Category.Category_Product_Low_Stock_Threshold):
                            product.Product_Stock_Status = 'Low Stock'
                        else:
                            product.Product_Stock_Status = 'Regular Stock'
                    product.save()

                    current_date = timezone.now()
                    Count_Edit_History.objects.create(
                        Date_Updated = current_date,
                        Initial_Inventory_Count = initial_count,
                        Updated_Inventory_Count = updated_count,
                        Image_Report = image_report,
                        Text_Report = text_report,
                        Product_ID = product,
                        Account_ID = cEdit_account
                    )
            messages.success(request, "Product count succesfully updated")
            return redirect('current_inventory')
    else:
        return render(request, 'inventoryapp/edit_count.html', {'products': products})

@login_required 
def inventory_update_history(request):
    Count_Edits = Count_Edit_History.objects.all()
    return render(request, 'inventoryapp/inventory_update_history.html',{'Count_Edits':Count_Edits})

@login_required 
def view_partially_fulfilled(request, pk):
    try:
        partially_fulfilled = Partially_Fulfilled_History.objects.get(pk=pk)
        response_data = {
            'partially_fulfill_edit_id': partially_fulfilled.Partially_Fulfill_Edit_ID,
            'date_updated': partially_fulfilled.Date_Updated.strftime("%Y-%m-%d %H:%M:%S"),
            'partially_fulfilled_quantity': partially_fulfilled.Partially_Fulfilled_Quantity,
            'image_report': partially_fulfilled.Image_Report.url if partially_fulfilled.Image_Report else None,
            'text_report': partially_fulfilled.Text_Report,
            'pro': partially_fulfilled.Stock.Product_Requisition_ID.Product_Requisition_ID,
            'product': partially_fulfilled.Stock.Product_ID.Name,
            'account_id': partially_fulfilled.Account_ID.user.username
        }
        return JsonResponse(response_data)
    except Partially_Fulfilled_History.DoesNotExist:
        return JsonResponse({'error': 'Partially Fulfilled Record not found'}, status=404)

@login_required 
def view_edit_count(request, pk):
    try:
        edit_count = Count_Edit_History.objects.get(pk=pk)
        response_data = {
            'edit_count_id': edit_count.Count_Edit_ID,
            'date_updated': edit_count.Date_Updated.strftime("%Y-%m-%d %H:%M:%S"),
            'initial_inventory_count': edit_count.Initial_Inventory_Count,
            'updated_inventory_count': edit_count.Updated_Inventory_Count,
            'image_report': edit_count.Image_Report.url if edit_count.Image_Report else None,
            'text_report': edit_count.Text_Report,
            'product': edit_count.Product_ID.Name,
            'account_id': edit_count.Account_ID.user.username
        }
        return JsonResponse(response_data)
    except Partially_Fulfilled_History.DoesNotExist:
        return JsonResponse({'error': 'Edit Count Record not found'}, status=404)