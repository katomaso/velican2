from django.contrib import admin
from .models import Category, Site, Page, Post, Publish

class PublishAdmin(admin.ModelAdmin):
    list_display = ("site", "preview", "success", "message")
    readonly_fields = ('started', 'finished', 'success', 'message')

# Register your models here.
admin.site.register(Site, admin.ModelAdmin)
admin.site.register(Category, admin.ModelAdmin)
admin.site.register(Page, admin.ModelAdmin)
admin.site.register(Post, admin.ModelAdmin)
admin.site.register(Publish, PublishAdmin)