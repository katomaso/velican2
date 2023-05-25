from django.contrib import admin
from .models import Category, Link, Site, Page, Post, Publish

class PublishAdmin(admin.ModelAdmin):
    list_display = ("site", "success", "finished", "message", "force")
    readonly_fields = ('started', 'finished', 'success', 'message')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "site")
    prepopulated_fields = {"slug": ("name",)}

class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "site", "slug", "draft")
    prepopulated_fields = {"slug": ("title",)}

class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "site", "slug")
    prepopulated_fields = {"slug": ("title",)}

class LinkAdmin(admin.ModelAdmin):
    list_display = ("title", "site")

# Register your models here.
admin.site.register(Site, admin.ModelAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Publish, PublishAdmin)