from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0003_alter_eventcategory_name_de_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="manual_occurrences",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Optional list of manual occurrence datetimes (ISO).",
            ),
        ),
    ]
