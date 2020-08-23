from django.contrib import admin
from django.utils.safestring import mark_safe

from shortify.models import Click, ShortenedURL


class ClickInline(admin.TabularInline):
    model = Click
    fields = ["time", "ip", "http_referer"]
    readonly_fields = fields
    can_delete = False

    def has_module_permission(self, *args, **kwargs):
        return True

    def has_view_permission(self, request, obj=None):
        return True


class ShortenedURLAdmin(admin.ModelAdmin):
    inlines = [
        ClickInline,
    ]

    fields = [
        "get_short_url",
        "short_path",
        "url",
        "is_active",
        "deactivate_at",
        "number_of_clicks",
        "max_clicks",
    ]
    readonly_fields = ["get_short_url", "number_of_clicks"]

    def get_short_url(self, obj):
        return mark_safe(f'<a href="{obj.short_url}">{obj.short_url}</a>')

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_module_permission(self, *args, **kwargs):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()


admin.site.register(ShortenedURL, ShortenedURLAdmin)
