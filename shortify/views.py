from django.db.models import F, Q
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.db import connection

from shortify.forms import URLForm
from shortify.models import Click, ShortenedURL


def index(request):
    if request.method == "POST":
        form = URLForm(request.POST)
        if form.is_valid():
            form.save()
            return render(
                request,
                "shortify/index.html",
                {"form": URLForm(), "short_url": form.instance.short_url,},
            )
    else:
        form = URLForm()
    return render(request, "shortify/index.html", {"form": form})


def redirect_short_to_long_url(request, short_path):
    try:
        shortened_url = ShortenedURL.objects.get(
            Q(pk=short_path),
            Q(is_active=True),
            Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
        )
        if shortened_url.max_clicks and shortened_url.max_clicks <= shortened_url.click_set.count():
            raise Http404
    except ShortenedURL.DoesNotExist:
        raise Http404

    Click.objects.create(
        shortened_url_id=short_path,
        ip=request.META.get("REMOTE_ADDR"),
        http_referer=request.META.get("HTTP_REFERER"),
    )
    return HttpResponsePermanentRedirect(shortened_url.url)
