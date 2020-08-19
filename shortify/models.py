from django.contrib.sites.models import Site
from django.db import models

from shortify.utils import gen_short_path


class ShortenedURL(models.Model):
    short_path = models.CharField(primary_key=True, max_length=6, default=gen_short_path)
    url = models.URLField(max_length=8190)
    is_active = models.BooleanField(default=True)

    @property
    def short_url(self):
        return f"http://{Site.objects.get_current().domain}/{self.short_path}/"


class Click(models.Model):
    shortened_url = models.ForeignKey(ShortenedURL, on_delete=models.RESTRICT)
    time = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True)
    http_referer = models.URLField(max_length=2048, null=True)
