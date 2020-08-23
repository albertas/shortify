from asgiref.sync import sync_to_async
from django.db import connection
from django.db.models import F, Q
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from shortify.forms import URLForm
from shortify.models import Click, ShortenedURL


def index(request):
    if request.method == "POST":
        form = URLForm(request.POST)
        if form.is_valid():
            shortened_url = form.save(commit=False)
            if request.user.is_authenticated:
                shortened_url.user = request.user
            shortened_url.save()
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
        url, max_clicks = ShortenedURL.objects.filter(
            Q(pk=short_path),
            Q(is_active=True),
            Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
        ).values_list("url", "max_clicks")[0]
        if max_clicks and max_clicks <= Click.objects.filter(shortened_url_id=short_path).count():
            raise Http404
    except IndexError:
        raise Http404

    Click.objects.create(
        shortened_url_id=short_path,
        ip=request.META.get("REMOTE_ADDR"),
        http_referer=request.META.get("HTTP_REFERER"),
    )
    return HttpResponsePermanentRedirect(url)


@sync_to_async
def get_url_max_clicks(short_path):
    url, max_clicks = ShortenedURL.objects.filter(
        Q(pk=short_path),
        Q(is_active=True),
        Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
    ).values_list("url", "max_clicks")[0]
    return url, max_clicks


@sync_to_async
def get_clicks(short_path):
    return Click.objects.filter(shortened_url_id=short_path).count()


@sync_to_async
def save_click(short_path, ip, http_referer):
    Click.objects.create(
        shortened_url_id=short_path, ip=ip, http_referer=http_referer,
    )


async def redirect_short_to_long_url_async(request, short_path):
    try:
        url, max_clicks = await get_url_max_clicks(short_path)
        if max_clicks and max_clicks <= await get_clicks(short_path):
            raise Http404
    except IndexError:
        raise Http404

    # TODO: should be possible not to await for completion of `save_click()` function,
    # however for some reason Click instance does not get created if await is omitted.
    # Should investigate further. Not awaiting would improve load time from 50ms to 30ms.
    await save_click(short_path, request.META.get("REMOTE_ADDR"), request.META.get("HTTP_REFERER"))
    return HttpResponsePermanentRedirect(url)
