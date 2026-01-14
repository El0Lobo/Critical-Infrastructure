from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("setup", "0005_sitesettings_dev_login_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="pos_apply_discounts",
            field=models.BooleanField(
                default=True,
                help_text="Allow item/order discounts to modify POS totals.",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pos_apply_tax",
            field=models.BooleanField(
                default=True,
                help_text="Apply tax to POS carts when calculating totals.",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pos_show_discounts",
            field=models.BooleanField(
                default=True,
                help_text="Show the Quick Discounts panel in the POS.",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pos_show_tax",
            field=models.BooleanField(
                default=True,
                help_text="Show tax rows in the POS UI.",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="pos_tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("19.00"),
                help_text="Default POS tax rate (%)",
                max_digits=5,
            ),
        ),
    ]

