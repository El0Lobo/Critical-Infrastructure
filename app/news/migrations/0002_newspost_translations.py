from __future__ import annotations

from django.db import migrations, models


def copy_default_language(apps, schema_editor):
    NewsPost = apps.get_model("news", "NewsPost")
    for post in NewsPost.objects.all():
        updates = {}
        if post.title and not getattr(post, "title_en", None):
            updates["title_en"] = post.title
        if post.slug and not getattr(post, "slug_en", None):
            updates["slug_en"] = post.slug
        if post.summary and not getattr(post, "summary_en", None):
            updates["summary_en"] = post.summary
        if post.body and not getattr(post, "body_en", None):
            updates["body_en"] = post.body
        if post.category and not getattr(post, "category_en", None):
            updates["category_en"] = post.category
        if updates:
            NewsPost.objects.filter(pk=post.pk).update(**updates)


def noop(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="newspost",
            name="title_en",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="title_es",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="title_de",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="title_fr",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="slug_en",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="slug_es",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="slug_de",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="slug_fr",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="summary_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="summary_es",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="summary_de",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="summary_fr",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="body_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="body_es",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="body_de",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="body_fr",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="category_en",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="category_es",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="category_de",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="newspost",
            name="category_fr",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.RunPython(copy_default_language, noop),
    ]

