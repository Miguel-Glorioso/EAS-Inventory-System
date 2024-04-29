# Generated by Django 5.0.2 on 2024-04-29 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0050_remove_account_first_name_remove_account_last_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consignee',
            name='Zip_Code',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='customer',
            name='Zip_Code',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='purchase_order',
            name='Order_Method',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]