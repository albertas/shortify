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
        url = ShortenedURL.objects.filter(
            Q(pk=short_path),
            Q(is_active=True),
            Q(deactivate_at__isnull=True) | Q(deactivate_at__gt=timezone.now()),
            Q(max_clicks__isnull=True) | Q(number_of_clicks__lt=F("max_clicks")),
        ).values_list("url", flat=True)[0]
    except IndexError:
        raise Http404

    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE shortify_shortenedurl "
                       f"SET number_of_clicks = number_of_clicks + 1 "
                       f"WHERE short_path = '{short_path}'")

    Click.objects.create(
        shortened_url_id=short_path,
        ip=request.META.get("REMOTE_ADDR"),
        http_referer=request.META.get("HTTP_REFERER"),
    )
    return HttpResponsePermanentRedirect(url)
