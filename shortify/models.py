from django.contrib.sites.models import Site
from django.db import models

from shortify.utils import gen_short_path


class ShortenedURL(models.Model):
    short_path = models.CharField(primary_key=True, max_length=6, default=gen_short_path)
    url = models.URLField(max_length=8190)

    def short_url(self):
        return f"http://{Site.objects.get_current().domain}/{self.short_path}/"
