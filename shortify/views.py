from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from shortify.forms import URLForm
from shortify.models import ShortenedURL


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


def redirect_to_url(request, short_path):
    shortened_url = get_object_or_404(ShortenedURL, pk=short_path)
    return HttpResponseRedirect(shortened_url.url)
