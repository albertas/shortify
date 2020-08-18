from django.shortcuts import render

from shortify.forms import URLForm


def index(request):
    form = URLForm()
    return render(request, "shortify/index.html", {"form": form})
