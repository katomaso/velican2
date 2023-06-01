from django.contrib import admin
from django.utils.translation import gettext as _

from .models import Theme, Settings, ThemeSettings


class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "downloaded", "installed", "url")
    readonly_fields = ("updated", "downloaded", "installed", "path", "log")
    actions = ["download", 'install', 'update']
    actions_on_top = True

    @admin.action(description=_('Download the URL'))
    def download(self, request, queryset):
        for object in queryset.all():
            object.download(save=True)

    @admin.action(description=_('Install into pelican'))
    def install(self, request, queryset):
        for object in queryset.all():
            object.install()

    @admin.action(description=_('Update repository'))
    def update(self, request, queryset):
        for object in queryset.all():
            object.update(recurse=True, save=True)


# Register your models here.
admin.site.register(Theme, ThemeAdmin)
admin.site.register(ThemeSettings, admin.ModelAdmin)
admin.site.register(Settings, admin.ModelAdmin)
