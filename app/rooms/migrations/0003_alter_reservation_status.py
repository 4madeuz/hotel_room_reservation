# Generated by Django 5.0 on 2023-12-19 10:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('rooms', '0002_rename_rentler_reservation_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='status',
            field=models.TextField(
                choices=[
                    ('booked', 'Booked'),
                    ('refused', 'Refused'),
                    ('active', 'Active'),
                    ('expired', 'Expired'),
                ],
                default='booked',
                verbose_name='status',
            ),
        ),
    ]
