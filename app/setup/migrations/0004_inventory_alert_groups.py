from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("setup", "0003_logo_filefields"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="inventory_dashboard_groups",
            field=models.ManyToManyField(
                blank=True,
                help_text="Users in these groups see inventory alerts on the dashboard. Leave empty to restrict to superusers.",
                related_name="inventory_dashboard_sites",
                to="auth.group",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="inventory_notification_groups",
            field=models.ManyToManyField(
                blank=True,
                help_text="Users in these groups receive inventory reorder messages. Leave empty to notify superusers only.",
                related_name="inventory_notification_sites",
                to="auth.group",
            ),
        ),
    ]
