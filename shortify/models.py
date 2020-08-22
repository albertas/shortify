from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection

from shortify.utils import gen_short_path


class ShortenedURL(models.Model):
    short_path = models.CharField(primary_key=True, max_length=6, default=gen_short_path)
    url = models.URLField(max_length=8190)
    is_active = models.BooleanField(default=True)
    deactivate_at = models.DateTimeField(null=True)
    number_of_clicks = models.PositiveIntegerField(default=0)
    max_clicks = models.PositiveIntegerField(null=True)

    @property
    def short_url(self):
        return f"http://{Site.objects.get_current().domain}/{self.short_path}/"


class Click(models.Model):
    shortened_url = models.ForeignKey(ShortenedURL, on_delete=models.RESTRICT)
    time = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True)
    http_referer = models.URLField(max_length=2048, null=True)


@receiver(post_save, sender=Click)
def increase_click_counter(sender, signal, instance, created, update_fields, **kwargs):
    if created:
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE shortify_shortenedurl "
                           f"SET number_of_clicks = number_of_clicks + 1 "
                           f"WHERE short_path = '{instance.shortened_url_id}'")
