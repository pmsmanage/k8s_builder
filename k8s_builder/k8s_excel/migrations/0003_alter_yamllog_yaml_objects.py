# Generated by Django 4.2.2 on 2023-06-14 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('k8s_excel', '0002_rename_yamllogs_yamllog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='yamllog',
            name='yaml_objects',
            field=models.JSONField(),
        ),
    ]
