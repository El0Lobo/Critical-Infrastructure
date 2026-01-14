from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0002_alter_page_is_visible_alter_page_render_body_only_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="layout_overrides",
            field=models.JSONField(blank=True, default=list, help_text="Languages that have a custom block layout override."),
        ),
    ]
