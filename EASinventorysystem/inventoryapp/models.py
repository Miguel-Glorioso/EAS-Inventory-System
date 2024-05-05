from django.db import models
from django.core.validators import MinValueValidator, MaxLengthValidator, MaxValueValidator
from django.contrib.auth.models import User


# Create your models here.
# will figure out how to make the images into their own folders
class Account(models.Model):
    Account_ID = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    Profile_Picture = models.ImageField(upload_to='account_pfps/', null=True, blank=True)
    First_Name = models.CharField(max_length=32)
    Last_Name = models.CharField(max_length=32)
    Role = models.CharField(max_length = 32)
    Visibility = models.BooleanField(default=True)

    def getUsername(self):
        return self.Username
    
    def getPassword(self):
        return self.Password
    
    def __str__(self):
        return str(self.user)

class Product(models.Model):
    Product_ID = models.AutoField(primary_key=True)            
    EAS_Product_ID = models.CharField(max_length=32, unique=True)
    Name = models.CharField(max_length=64)
    Picture = models.ImageField(null=True, blank=True, upload_to='product_images/', )
    SKU = models.CharField(max_length=32)
    Price = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
    Actual_Inventory_Count = models.PositiveIntegerField(validators =[MaxValueValidator(99999)])
    Reserved_Inventory_Count = models.PositiveIntegerField(validators =[MaxValueValidator(99999)], default = 0)
    To_Be_Received_Inventory_Count = models.PositiveIntegerField(validators =[MaxValueValidator(99999)], default = 0)
    Visibility = models.BooleanField(default=True)
    Product_Low_Stock_Threshold = models.PositiveIntegerField(validators =[MaxValueValidator(99999)], null=True, blank=True)
    Product_Stock_Status = models.CharField(max_length=16) 
    Category = models.ForeignKey("Category", on_delete=models.PROTECT)

    def __str__(self):
        return self.Name

class Category(models.Model):
    Category_ID = models.AutoField(primary_key=True)
    Category_Name = models.CharField(max_length=32, unique=True)
    Category_Hex_Color_ID = models.CharField(max_length=7, unique=True)
    Description = models.TextField(validators =[MaxLengthValidator(1024)])
    Category_Product_Low_Stock_Threshold = models.PositiveIntegerField(validators =[MaxValueValidator(99999)])
    Notes = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)

    def __str__(self):
        return self.Category_Name
    
class Purchase_Order(models.Model):
    Purchase_Order_ID = models.AutoField(primary_key=True)
    Creation_Date = models.DateTimeField()
    Requested_Date = models.DateField()
    Fulfilled_Date = models.DateTimeField(null=True, blank=True)
    Total_Due = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    Notes = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)
    Progress = models.CharField(max_length=16, default = "Pending")
    PO_Status = models.CharField(max_length=16, default = "Unfulfilled")
    Shipping_Method = models.CharField(max_length=32)
    Order_Method = models.CharField(max_length=32,  null=True, blank=True)
    Customer_ID = models.ForeignKey('Customer', on_delete=models.PROTECT, null=True, blank=True) #null if it is a consignee
    Consignee_ID = models.ForeignKey('Consignee', on_delete=models.PROTECT, null=True, blank=True) #null if it is a customer
    Account_ID_Closed_by = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='po_closed', null=True, blank=True)
    Account_ID_Created_by = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='po_created')
    
    def __str__(self):
        return f" Purchase Order # {self.Purchase_Order_ID}"

class Product_Ordered(models.Model):
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Purchase_Order_ID = models.ForeignKey(Purchase_Order, on_delete=models.PROTECT)
    Quantity = models.PositiveIntegerField( validators=[MaxValueValidator(99999)])

    def __str__(self):
        return f"{self.Product_ID.Name} in {self.Purchase_Order_ID} "
    
class Product_Requisition_Order(models.Model):
    Product_Requisition_ID = models.AutoField(primary_key=True)
    Creation_Date = models.DateTimeField()
    Estimated_Receiving_Date = models.DateField()
    Received_Date = models.DateTimeField(null=True, blank=True)
    PRO_Manufacturer = models.CharField(max_length=32)
    Total_Cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    Notes = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)
    Progress = models.CharField(max_length=16, default = "Pending")
    PRO_Status = models.CharField(max_length=16, default = "Ongoing")
    Account_ID_Closed_by = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='pro_closed', null=True, blank=True)
    Account_ID_Created_by = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='pro_created')
    
    def __str__(self):
        return f" Product Requisition Order # {self.Product_Requisition_ID}"
    
class Stock_Ordered(models.Model):
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Product_Requisition_ID = models.ForeignKey(Product_Requisition_Order, on_delete=models.PROTECT)
    Quantity = models.PositiveIntegerField( validators=[MaxValueValidator(99999)])
    
    def __str__(self):
        return f"{self.Product_ID.Name} in {self.Product_Requisition_ID} "

class Customer(models.Model):
    Customer_ID = models.AutoField(primary_key=True)
    Customer_Name = models.CharField(max_length=32)
    Address_Line_1 = models.CharField(max_length=128)
    Barangay = models.CharField(max_length=64)
    Municipality = models.CharField(max_length=64)
    Province = models.CharField(max_length=64)
    Zip_Code = models.CharField(max_length=4)
    Primary_Contact_Number = models.CharField(max_length=11)
    Customer_Type = models.CharField(max_length=16)
    Notes = models.TextField(null=True, blank=True, validators=[MaxLengthValidator(1024)])

    def __str__(self):
        return self.Customer_Name
    
class Consignee(models.Model):
    Consignee_ID = models.AutoField(primary_key=True)
    Consignee_Tag_ID = models.CharField(max_length=32, unique=True)
    Consignee_Name = models.CharField(max_length=32, unique=True)
    Address_Line_1 = models.CharField(max_length=128)
    Barangay = models.CharField(max_length=64)
    Municipality = models.CharField(max_length=64)
    Province = models.CharField(max_length=64)
    Zip_Code = models.CharField(max_length=4)
    Primary_Contact_Number = models.CharField(max_length=11)
    Customer_Type = models.CharField(max_length=16)
    Notes = models.TextField(null=True, blank=True, validators=[MaxLengthValidator(1024)])
    Consignment_Period_Start = models.DateField()
    Consignment_Period_End = models.DateField()
    Emergency_Contact_Number = models.CharField(max_length=11,null=True, blank=True)
    Email_Address = models.EmailField(max_length=128)
    Tag_Hex_Color_ID = models.CharField(max_length=7, unique=True)

    def __str__(self):
        return self.Consignee_Name
    
class Consignee_Product(models.Model):
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Consignee_ID = models.ForeignKey(Consignee, on_delete=models.PROTECT)
    
    def getConsignee_Tag(self):
        return self.Consignee_ID.Consignee_Tag_ID
    
    def __str__(self):
        return f"{self.Product_ID.Name} Consignee: {self.Consignee_ID.Consignee_Tag_ID}"

class Count_Edit_History(models.Model):
    Count_Edit_ID = models.AutoField(primary_key=True)
    Date_Updated = models.DateTimeField()
    Initial_Inventory_Count = models.PositiveIntegerField(validators=[MaxValueValidator(99999)])
    Updated_Inventory_Count = models.PositiveIntegerField(validators=[MaxValueValidator(99999)])
    Image_Report = models.ImageField(upload_to='count_edit_images/', null=True, blank=True)
    Text_Report = models.TextField(validators=[MaxLengthValidator(1024)])
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Account_ID = models.ForeignKey(Account, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"Count Edit #{self.Count_Edit_ID} Product: {self.Product_ID}"

class Partially_Fulfilled_History(models.Model):
    Partially_Fulfill_Edit_ID = models.AutoField(primary_key=True)
    Date_Updated = models.DateTimeField()
    Partially_Fulfilled_Quantity = models.PositiveIntegerField(validators=[MaxValueValidator(99999)])
    Image_Report = models.ImageField(upload_to='partially_fulfilled_images/', null=True, blank=True)
    Text_Report = models.TextField(validators =[MaxLengthValidator(1024)])
    Stock = models.ForeignKey(Stock_Ordered, on_delete=models.PROTECT)
    Account_ID = models.ForeignKey(Account, on_delete=models.PROTECT)
    
    def __str__(self):
        return f" Partial fulfill #{self.Partially_Fulfill_Edit_ID} for {self.Stock}"