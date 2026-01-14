from django.contrib.sitemaps import Sitemap

from .models import Band


class BandSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Band.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at
