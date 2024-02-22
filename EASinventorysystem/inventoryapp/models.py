from django.db import models
from django.core.validators import MinValueValidator, MaxLengthValidator, MaxValueValidator


# Create your models here.
# will figure out how to make the images into their own folders
class Account(models.Model):
    Account_ID = models.AutoField(primary_key=True)
    Username = models.CharField(max_length = 64)
    Password = models.CharField(max_length = 32)
    First_name = models.CharField(max_length = 32)
    Last_name = models.CharField(max_length = 32)
    Profile_Picture = models.ImageField(upload_to='account_pfps/', null=True, blank=True)
    Role = models.CharField(max_length = 32)

    def getUsername(self):
        return self.Username
    
    def getPassword(self):
        return self.Password
    
    def __str__(self):
        return str(self.First_name) + " " + str(self.Last_name)

class Product(models.Model):
    Product_ID = models.AutoField(primary_key=True)            
    EAS_Product_ID = models.CharField(max_length=32, unique=True)
    Name = models.CharField(max_length=64)
    Picture = models.ImageField(null=True, blank=True, upload_to='product_images/', )
    SKU = models.CharField(max_length=32)
    Price = models.DecimalField(max_digits=7, decimal_places=2, validators=[MinValueValidator(0)])
    Actual_Inventory_Count = models.PositiveIntegerField(validators =[MaxValueValidator(9999)])
    Reserved_Inventory_Count = models.PositiveIntegerField(validators =[MaxValueValidator(9999)], default = 0)
    To_Be_Received_Inventory_Count = models.PositiveIntegerField(validators =[MaxValueValidator(9999)], default = 0)
    Visibility = models.BooleanField(default=True)
    Product_Low_Stock_Threshold = models.PositiveIntegerField(validators =[MaxValueValidator(9999)], null=True, blank=True)
    Product_Stock_Status = models.CharField(max_length=16) # needs implementation
    Category = models.ForeignKey("Category", on_delete=models.PROTECT)

    def __str__(self):
        return self.Name

class Category(models.Model):
    Category_ID = models.AutoField(primary_key=True)
    Category_Name = models.CharField(max_length=32)
    Category_Hex_Color_ID = models.CharField(max_length=7)
    Description = models.TextField(validators =[MaxLengthValidator(1024)])
    Category_Product_Low_Stock_Threshold = models.PositiveIntegerField(validators =[MaxValueValidator(9999)])
    Notes = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)

    def __str__(self):
        return self.Category_Name
    
class Purchase_Order(models.Model):
    Purchase_Order_ID = models.AutoField(primary_key=True)
    Creation_Date = models.DateTimeField(auto_now_add=True)
    Requested_Date = models.DateField(null=True, blank=True)
    Fulfilled_Date = models.DateTimeField(null=True, blank=True)
    Total_Due = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    Notes = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)
    Progress = models.CharField(max_length=16, default = "Pending")
    PO_Status = models.CharField(max_length=16, default = "Unfulfilled")
    Shipping_Method = models.CharField(max_length=32)
    Order_Method = models.CharField(max_length=32)
    Customer_ID = models.ForeignKey('Customer', on_delete=models.PROTECT, null=True, blank=True) #null if it is a consignee
    Consignee_ID = models.ForeignKey('Consignee', on_delete=models.PROTECT, null=True, blank=True) #null if it is a customer
    Account_ID = models.ForeignKey(Account, on_delete=models.PROTECT)

    def __str__(self):
        return 

class Products_Ordered(models.Model):
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Purchase_Order_ID = models.ForeignKey(Purchase_Order, on_delete=models.PROTECT)
    Quantity = models.PositiveIntegerField( validators=[MaxValueValidator(9999)])

    def __str__(self):
        return 
    
class Product_Requisition_Order(models.Model):
    Product_Requisition_ID = models.AutoField(primary_key=True)
    Creation_Date = models.DateTimeField(auto_now_add=True)
    Estimated_Receiving_Date = models.DateField( null=True, blank=True)
    Received_Date = models.DateTimeField(null=True, blank=True)
    PRO_Manufacturer = models.CharField(max_length=32)
    Total_Cost = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    Notes = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)
    Progress = models.CharField(max_length=16, default = "Pending")
    PRO_Status = models.CharField(max_length=16, default = "Ongoing")
    Account_ID = models.ForeignKey(Account, on_delete=models.PROTECT)
    
    def __str__(self):
        return 
    
class Stocks_Ordered(models.Model):
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Product_Requisition_ID = models.ForeignKey(Product_Requisition_Order, on_delete=models.PROTECT)
    Quantity = models.PositiveIntegerField( validators=[MaxValueValidator(9999)])

    def __str__(self):
        return 

class Customer(models.Model):
    Customer_ID = models.AutoField(primary_key=True)
    Customer_Name = models.CharField(max_length=32)
    Address_Line_1 = models.CharField(max_length=128)
    Barangay = models.CharField(max_length=64)
    Municipality = models.CharField(max_length=64)
    Province = models.CharField(max_length=64)
    Zip_Code = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    Primary_Contact_Number = models.CharField(max_length=11)
    Customer_Type = models.CharField(max_length=16)
    Notes = models.TextField(null=True, blank=True, validators=[MaxLengthValidator(1024)])

    def __str__(self):
        return self.Customer_Name
    
class Consignee(models.Model):
    Consignee_ID = models.AutoField(primary_key=True)
    Consignee_Tag_ID = models.CharField(max_length=32)
    Customer_Name = models.CharField(max_length=32)
    Address_Line_1 = models.CharField(max_length=128)
    Barangay = models.CharField(max_length=64)
    Municipality = models.CharField(max_length=64)
    Province = models.CharField(max_length=64)
    Zip_Code = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    Primary_Contact_Number = models.CharField(max_length=11)
    Customer_Type = models.CharField(max_length=16)
    Notes = models.TextField(null=True, blank=True, validators=[MaxLengthValidator(1024)])
    Consignment_Period_Start = models.DateField()
    Consignment_Period_End = models.DateField()
    Emergency_Contact_Number = models.CharField(max_length=11)
    Email_Address = models.EmailField(max_length=128)
    Tag_Hex_Color_ID = models.CharField(max_length=7)

    def __str__(self):
        return self.Customer_Name
    
class Consignee_Product(models.Model):
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Consignee_ID = models.ForeignKey(Consignee, on_delete=models.PROTECT)
    
    def getConsignee_Tag(self):
        return self.Consignee_ID.Consignee_Tag_ID
    
    def __str__(self):
        return f"{self.Product_ID.Name} Consignee: {self.Consignee_ID.Consignee_Tag_ID}"

class Count_Edit_History(models.Model):
    Count_Edit_ID = models.AutoField(primary_key=True)
    Date_Updated = models.DateTimeField(auto_now_add=True)
    Initial_Inventory_Count = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    Updated_Inventory_Count = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    Image_Report = models.ImageField(upload_to='count_edit_images/', null=True, blank=True, )
    Text_Report = models.TextField(null=True, blank=True, validators=[MaxLengthValidator(1024)])
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Account_ID = models.ForeignKey(Account, on_delete=models.PROTECT)
    
    def __str__(self):
        return 

class Partially_Fulfilled_History(models.Model):
    Partially_Fulfill_Edit_ID = models.AutoField(primary_key=True)
    Date_Updated = models.DateTimeField(auto_now_add=True)
    Partially_Fulfilled_Quantity = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    Image_Report = models.ImageField(upload_to='partially_fulfilled_images/', null=True, blank=True)
    Text_Report = models.TextField(validators =[MaxLengthValidator(1024)], null=True, blank=True)
    Product_ID = models.ForeignKey(Product, on_delete=models.PROTECT)
    Product_Requisition_ID = models.ForeignKey(Product_Requisition_Order, on_delete=models.PROTECT)
    Account_ID = models.ForeignKey(Account, on_delete=models.PROTECT)
    
    def __str__(self):
        return 