# Generated by Django 4.2.2 on 2023-06-14 08:21

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('k8s_excel', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='YamlLogs',
            new_name='YamlLog',
        ),
    ]
