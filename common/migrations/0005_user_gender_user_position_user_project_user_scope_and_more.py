# Generated by Django 4.2.4 on 2023-08-29 07:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0004_rename_username_user_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="gender",
            field=models.CharField(
                choices=[("male", "男"), ("female", "女")], default="男", max_length=32
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="position",
            field=models.CharField(default=56, max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="project",
            field=models.CharField(default=5, max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="scope",
            field=models.CharField(default=6, max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="user",
            name="account",
            field=models.CharField(max_length=128, unique=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="nickname",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="user",
            name="password",
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name="user",
            name="phonenumber",
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
