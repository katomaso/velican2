from django.contrib import admin
from django.utils.translation import gettext as _

from .models import Theme, Plugin, Settings, ThemeSettings


class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "downloaded", "installed", "category", "url")
    readonly_fields = ("updated", "downloaded", "installed", "path", "log")
    actions = ["download", 'install', 'update', 'reload']
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

    @admin.action(description=_('Refresh images and README'))
    def reload(self, request, queryset):
        for object in queryset.all():
            object.reload(save=True)

class PluginAdmin(admin.ModelAdmin):
    list_display = ("id", "default")
    readonly_fields = ("name", )

class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ("theme", "pelican")

# Register your models here.
admin.site.register(Theme, ThemeAdmin)
admin.site.register(ThemeSettings, ThemeSettingsAdmin)
admin.site.register(Settings, admin.ModelAdmin)
admin.site.register(Plugin, PluginAdmin)
