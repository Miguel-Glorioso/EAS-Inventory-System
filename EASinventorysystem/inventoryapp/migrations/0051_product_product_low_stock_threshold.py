# Generated by Django 4.2.10 on 2024-04-29 07:41

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0050_remove_product_product_low_stock_threshold'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='Product_Low_Stock_Threshold',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(99999)]),
        ),
    ]
