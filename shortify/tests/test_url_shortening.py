from datetime import datetime, timedelta
from random import seed
from unittest.mock import patch

import pytz
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from shortify.models import ShortenedURL


@patch("django.utils.timezone.now", return_value=datetime(2020, 1, 1, tzinfo=pytz.utc))
class TestULRShortening(TestCase):
    def setUp(self):
        seed("test seed")

    def test_index_page(self, *args):
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 200)

    def test_shortening_url(self, *args):
        resp = self.client.post(reverse("index"), data={"url": "http://example.com/"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Your shortened URL is:", resp.content)
        self.assertIn(b"http://localhost:8000/KOs6o7/", resp.content)

        # Test successful redirection from shortened url
        resp = self.client.get("http://localhost:8000/KOs6o7/")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

    def test_opening_none_existing_shortened_url(self, *args):
        resp = self.client.get("http://localhost:8000/ABC123/")
        self.assertEqual(resp.status_code, 404)

    def test_shortening_without_provided_url(self, *args):
        resp = self.client.post(reverse("index"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist"', resp.content)
        self.assertIn(b"This field is required", resp.content)

    def test_shortening_invalid_url(self, *args):
        resp = self.client.post(reverse("index"), data={"url": "not_url"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist"', resp.content)
        self.assertIn(b"Enter a valid URL", resp.content)

    def test_shortening_too_long_url(self, *args):
        resp = self.client.post(reverse("index"), data={"url": f'http://example.com/{"a"*8300}'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist"', resp.content)
        self.assertIn(b"Ensure this value has at most 8190 characters", resp.content)

    def test_shortened_url_deactivation(self, *args):
        short_url_instance = ShortenedURL.objects.create(
            short_path="KOs6o7", url="http://example.com/"
        )
        short_url = short_url_instance.short_url

        resp = self.client.get(short_url)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

        short_url_instance.is_active = False
        short_url_instance.save()

        resp = self.client.get(short_url)
        self.assertEqual(resp.status_code, 404)

    def test_click_information_logging(self, *args):
        short_url_instance = ShortenedURL.objects.create(
            short_path="KOs6o7", url="http://example.com/"
        )
        self.assertEqual(short_url_instance.click_set.count(), 0)

        headers = {
            "HTTP_REFERER": "https://secret.com/",
            "REMOTE_ADDR": "1.1.1.1",
        }

        resp = self.client.get(short_url_instance.short_url, **headers)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

        self.assertEqual(short_url_instance.click_set.count(), 1)
        click = short_url_instance.click_set.first()
        self.assertEqual(click.time, datetime(2020, 1, 1, tzinfo=pytz.utc))
        self.assertEqual(click.ip, "1.1.1.1")
        self.assertEqual(click.http_referer, "https://secret.com/")

    def test_click_information_logging_when_referer_unavailable(self, *args):
        short_url_instance = ShortenedURL.objects.create(
            short_path="KOs6o7", url="http://example.com/"
        )
        self.assertEqual(short_url_instance.click_set.count(), 0)

        headers = {
            "REMOTE_ADDR": "1.1.1.1",
        }

        resp = self.client.get(short_url_instance.short_url, **headers)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

        self.assertEqual(short_url_instance.click_set.count(), 1)
        click = short_url_instance.click_set.first()
        self.assertEqual(click.time, datetime(2020, 1, 1, tzinfo=pytz.utc))
        self.assertEqual(click.ip, "1.1.1.1")
        self.assertEqual(click.http_referer, None)

    def test_shortened_url_deactivate_at_option_usage(self, *args):
        short_url_instance = ShortenedURL.objects.create(
            short_path="KOs6o7", url="http://example.com/"
        )
        self.assertEqual(short_url_instance.deactivate_at, None)

        resp = self.client.get(short_url_instance.short_url)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

        short_url_instance.deactivate_at = timezone.now() + timedelta(hours=1)
        short_url_instance.save()

        resp = self.client.get(short_url_instance.short_url)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

        short_url_instance.deactivate_at = timezone.now() - timedelta(hours=1)
        short_url_instance.save()

        resp = self.client.get(short_url_instance.short_url)
        self.assertEqual(resp.status_code, 404)

    def test_deactivate_shortened_url_after_max_clicks(self, *args):
        shortened_url = ShortenedURL.objects.create(
            short_path="KOs6o7", url="http://example.com/", max_clicks=2,
        )
        self.assertEqual(shortened_url.deactivate_at, None)
        self.assertEqual(shortened_url.number_of_clicks, 0)

        resp = self.client.get(shortened_url.short_url)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")
        shortened_url.refresh_from_db()
        self.assertEqual(shortened_url.number_of_clicks, 1)

        resp = self.client.get(shortened_url.short_url)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")
        shortened_url.refresh_from_db()
        self.assertEqual(shortened_url.number_of_clicks, 2)

        resp = self.client.get(shortened_url.short_url)
        self.assertEqual(resp.status_code, 404)
        shortened_url.refresh_from_db()
        self.assertEqual(shortened_url.number_of_clicks, 2)
