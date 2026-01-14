from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="url",
            field=models.URLField(blank=True, null=True, help_text="External link or embed URL"),
        ),
    ]
