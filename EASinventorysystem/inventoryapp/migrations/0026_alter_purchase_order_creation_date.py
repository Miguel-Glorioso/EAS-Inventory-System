# Generated by Django 5.0.2 on 2024-03-14 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0025_rename_products_ordered_product_ordered_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase_order',
            name='Creation_Date',
            field=models.DateTimeField(),
        ),
    ]
