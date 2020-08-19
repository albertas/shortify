from datetime import datetime
from random import seed
from unittest.mock import patch

import pytz
from django.test import TestCase
from django.urls import reverse

from shortify.models import ShortenedURL


class TestULRShortening(TestCase):
    def setUp(self):
        seed("test seed")

    def test_index_page(self):
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 200)

    def test_shortening_url(self):
        resp = self.client.post(reverse("index"), data={"url": "http://example.com/"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Your shortened URL is:", resp.content)
        self.assertIn(b"http://localhost:8000/eKOs6o/", resp.content)

        # Test successful redirection from shortened url
        resp = self.client.get("http://localhost:8000/eKOs6o/")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

    def test_opening_none_existing_shortened_url(self):
        resp = self.client.get("http://localhost:8000/ABC123/")
        self.assertEqual(resp.status_code, 404)

    def test_shortening_without_provided_url(self):
        resp = self.client.post(reverse("index"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist"', resp.content)
        self.assertIn(b"This field is required", resp.content)

    def test_shortening_invalid_url(self):
        resp = self.client.post(reverse("index"), data={"url": "not_url"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist"', resp.content)
        self.assertIn(b"Enter a valid URL", resp.content)

    def test_shortening_too_long_url(self):
        resp = self.client.post(reverse("index"), data={"url": f'http://example.com/{"a"*8300}'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'class="errorlist"', resp.content)
        self.assertIn(b"Ensure this value has at most 8190 characters", resp.content)

    def test_shortened_url_deactivation(self):
        short_url_instance = ShortenedURL.objects.create(
            short_path="eKOs6o", url="http://example.com/"
        )
        short_url = short_url_instance.short_url

        resp = self.client.get(short_url)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp.url, "http://example.com/")

        short_url_instance.is_active = False
        short_url_instance.save()

        resp = self.client.get(short_url)
        self.assertEqual(resp.status_code, 404)

    @patch("django.utils.timezone.now", return_value=datetime(2020, 1, 1, tzinfo=pytz.utc))
    def test_click_information_logging(self, *args):
        short_url_instance = ShortenedURL.objects.create(
            short_path="eKOs6o", url="http://example.com/"
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
