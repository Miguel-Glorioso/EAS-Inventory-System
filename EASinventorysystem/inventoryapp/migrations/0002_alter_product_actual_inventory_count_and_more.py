# Generated by Django 5.0.1 on 2024-01-31 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='Actual_Inventory_Count',
            field=models.SmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='product',
            name='Category',
            field=models.CharField(max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='Consignee',
            field=models.CharField(max_length=4, null=True),
        ),
    ]
