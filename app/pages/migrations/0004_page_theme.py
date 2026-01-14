from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0003_page_layout_overrides"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="theme",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Global styling tokens (fonts/colors) applied to this page.",
            ),
        ),
    ]
