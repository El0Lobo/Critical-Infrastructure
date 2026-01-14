from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0001_initial"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryPackage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "label",
                    models.CharField(max_length=120),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=3,
                        help_text="How many base units are contained in this package (e.g., 750 mL for a bottle, 4500 mL for a case of six).",
                        max_digits=12,
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Use this package as the default suggestion when reordering.",
                    ),
                ),
                ("notes", models.CharField(blank=True, default="", max_length=255)),
                (
                    "inventory_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="packages",
                        to="inventory.inventoryitem",
                    ),
                ),
                (
                    "unit",
                    models.ForeignKey(
                        blank=True,
                        help_text="Optional unit override for display.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="menu.unit",
                    ),
                ),
            ],
            options={
                "ordering": ["label"],
            },
        ),
    ]
