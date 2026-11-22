"""Add a second address field for cleanup command tests."""

from django.db import migrations

from django_geoaddress.fields import GeoaddressField


class Migration(migrations.Migration):
    dependencies = [
        ('app', '0003_locationreadonly_addressbook'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='secondary_address',
            field=GeoaddressField(blank=True, null=True),
        ),
    ]
