# Generated by Django 3.0.5 on 2020-04-19 16:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_ddns', '0005_extradnsname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='extradnsname',
            name='reverse_action',
        ),
        migrations.RemoveField(
            model_name='extradnsname',
            name='reverse_rcode',
        ),
    ]
