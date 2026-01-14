from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("setup", "0002_logo_secondary_icon_pack_filename"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="logo",
            field=models.FileField(blank=True, null=True, upload_to="logos/"),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="logo_secondary",
            field=models.FileField(blank=True, null=True, upload_to="logos/"),
        ),
    ]
