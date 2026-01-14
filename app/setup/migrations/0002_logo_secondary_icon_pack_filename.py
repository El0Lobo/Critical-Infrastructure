from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("setup", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="icon_pack_filename",
            field=models.CharField(
                blank=True, help_text="Last uploaded icon pack filename.", max_length=255
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="logo_secondary",
            field=models.ImageField(blank=True, null=True, upload_to="logos/"),
        ),
    ]
