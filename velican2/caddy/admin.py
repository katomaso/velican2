from django.contrib import admin
from .models import Settings

class CaddySettings(admin.ModelAdmin):
    readonly_fields = ("admin_url")

# Register your models here.
admin.register(Settings, CaddySettings)