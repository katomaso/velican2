from django.contrib import admin
from django.utils.translation import gettext as _

from .models import Theme, ThemeSource, Engine


class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "installed", "updated")
    readonly_fields = ("installed", "updated", "log")
    actions = ['install', 'update', ]

    @admin.action(description=_('Install selected theme(s)'))
    def install(self, request, queryset):
        for object in queryset.all():
            object.install(save=True)

    @admin.action(description=_('Update selected theme(s)'))
    def update(self, request, queryset):
        for object in queryset.all():
            object.update(save=True)

class ThemeSourceAdmin(admin.ModelAdmin):
    list_display = ("url", "multiple", "downloaded", "installed")
    readonly_fields = ("updated", "downloaded", "installed", "path", "log")
    actions = ['install', 'update', "download", "clear"]
    actions_on_top = True

    @admin.action(description=_('Download the reposiotry using git clone'))
    def download(self, request, queryset):
        for object in queryset.all():
            object.download(save=True)

    @admin.action(description=_('Create a Theme object from the cloned repository'))
    def install(self, request, queryset):
        for object in queryset.all():
            object.install(save=True)

    @admin.action(description=_('Update the repository by running git pull'))
    def update(self, request, queryset):
        for object in queryset.all():
            object.update(recurse=True, save=True)

    @admin.action(description=_('Remove cloned directory and reset source state'))
    def clear(self, request, queryset):
        for object in queryset.all():
            object.clear(save=True)

# Register your models here.
admin.site.register(Theme, ThemeAdmin)
admin.site.register(ThemeSource, ThemeSourceAdmin)
admin.site.register(Engine, admin.ModelAdmin)
