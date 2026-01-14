from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0004_page_theme"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="custom_css",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="page",
            name="custom_js",
            field=models.TextField(blank=True, default=""),
        ),
    ]
