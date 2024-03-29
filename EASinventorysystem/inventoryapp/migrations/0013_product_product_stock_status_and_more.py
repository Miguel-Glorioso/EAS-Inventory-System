# Generated by Django 5.0.1 on 2024-02-08 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0012_category_consignee_customer_consignee_product_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='Product_Stock_Status',
            field=models.CharField(default='regular stock', max_length=16),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='account',
            name='Profile_Picture',
            field=models.ImageField(blank=True, null=True, upload_to='account_pfps/'),
        ),
        migrations.AlterField(
            model_name='count_edit_history',
            name='Image_Report',
            field=models.ImageField(blank=True, null=True, upload_to='count_edit_images/'),
        ),
        migrations.AlterField(
            model_name='partially_fulfilled_history',
            name='Image_Report',
            field=models.ImageField(blank=True, null=True, upload_to='partially_fulfilled_images/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='Picture',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/'),
        ),
    ]
