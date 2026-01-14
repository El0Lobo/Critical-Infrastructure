from django.db import migrations, models
from django.db.models import Q


def set_generic_kind(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    Category.objects.filter(Q(kind__isnull=True) | Q(kind="")).update(kind="generic")


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0002_alter_unitgroup_name_de_alter_unitgroup_name_en_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="kind",
            field=models.CharField(
                blank=True,
                choices=[
                    ("generic", "General"),
                    ("drink", "Drink"),
                    ("food", "Food"),
                ],
                default="generic",
                max_length=16,
            ),
        ),
        migrations.RunPython(set_generic_kind, migrations.RunPython.noop),
    ]
