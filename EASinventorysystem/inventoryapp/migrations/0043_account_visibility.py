# Generated by Django 5.0.2 on 2024-04-29 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryapp', '0042_alter_consignee_consignee_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='Visibility',
            field=models.BooleanField(default=True),
        ),
    ]
