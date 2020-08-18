from django import forms

from shortify.models import ShortenedURL


class URLForm(forms.ModelForm):
    class Meta:
        model = ShortenedURL
        fields = ["url"]
