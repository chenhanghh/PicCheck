# Generated by Django 4.2.4 on 2023-08-29 07:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0008_remove_user_gender_remove_user_position_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="account",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="user",
            name="nickname",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="user",
            name="password",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="user",
            name="phonenumber",
            field=models.CharField(max_length=200),
        ),
    ]
