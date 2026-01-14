from django.db import migrations

import app.core.encryption


class Migration(migrations.Migration):
    dependencies = [
        ("setup", "0006_pos_settings_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sitesettings",
            name="logo_secondary",
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="address_state",
            field=app.core.encryption.EncryptedCharField(blank=True, max_length=120),
        ),
    ]
