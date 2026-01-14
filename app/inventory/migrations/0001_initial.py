from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("menu", "0001_initial"),
        ("merch", "0001_initial"),
        ("pos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(blank=True, max_length=180, unique=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="children",
                        to="inventory.inventorycategory",
                    ),
                ),
            ],
            options={"ordering": ["sort_order", "name"]},
        ),
        migrations.CreateModel(
            name="InventoryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("ingredient", "Ingredient"),
                            ("supply", "Supply"),
                            ("asset", "Asset"),
                            ("product", "Product"),
                        ],
                        default="supply",
                        max_length=20,
                    ),
                ),
                ("description", models.TextField(blank=True, default="")),
                ("location", models.CharField(blank=True, default="", max_length=160)),
                ("unit_label", models.CharField(blank=True, default="", max_length=32)),
                (
                    "pack_quantity",
                    models.DecimalField(
                        decimal_places=3,
                        default=Decimal("1.000"),
                        help_text="Quantity delivered per pack (e.g., 30 for a 30L keg).",
                        max_digits=10,
                    ),
                ),
                (
                    "current_stock",
                    models.DecimalField(decimal_places=3, default=Decimal("0.000"), max_digits=12),
                ),
                (
                    "desired_stock",
                    models.DecimalField(decimal_places=3, default=Decimal("0.000"), max_digits=12),
                ),
                (
                    "reorder_point",
                    models.DecimalField(decimal_places=3, default=Decimal("0.000"), max_digits=12),
                ),
                ("needs_reorder", models.BooleanField(default=False)),
                (
                    "auto_track_sales",
                    models.BooleanField(
                        default=False,
                        help_text="When enabled, POS sales linked to this item will reduce stock automatically.",
                    ),
                ),
                ("public_visible", models.BooleanField(default=False)),
                ("public_description", models.TextField(blank=True, default="")),
                ("public_url", models.URLField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("last_reorder_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="items",
                        to="inventory.inventorycategory",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_items_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "menu_items",
                    models.ManyToManyField(blank=True, related_name="inventory_links", to="menu.item"),
                ),
                (
                    "merch_products",
                    models.ManyToManyField(blank=True, related_name="inventory_links", to="merch.product"),
                ),
                (
                    "pack_unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_pack_items",
                        to="menu.unit",
                    ),
                ),
                (
                    "unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_items",
                        to="menu.unit",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_items_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="InventoryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("change_amount", models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("manual", "Manual adjustment"),
                            ("pos", "POS sale"),
                            ("restock", "Restock"),
                            ("reorder_flag", "Reorder flag"),
                        ],
                        max_length=20,
                    ),
                ),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_logs_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "inventory_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="logs", to="inventory.inventoryitem"
                    ),
                ),
                (
                    "sale_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory_logs",
                        to="pos.saleitem",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="InventoryConsumption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity_per_sale", models.DecimalField(decimal_places=3, max_digits=10)),
                (
                    "inventory_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="menu_consumptions",
                        to="inventory.inventoryitem",
                    ),
                ),
                (
                    "menu_variant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory_consumptions",
                        to="menu.itemvariant",
                    ),
                ),
            ],
            options={"ordering": ["menu_variant"]},
        ),
        migrations.AddConstraint(
            model_name="inventorylog",
            constraint=models.UniqueConstraint(
                condition=models.Q(("sale_item__isnull", False)),
                fields=("inventory_item", "sale_item"),
                name="inventory_log_unique_sale",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="inventoryconsumption",
            unique_together={("inventory_item", "menu_variant")},
        ),
    ]
