from django.contrib import admin
from .models import Theme, Settings

# Register your models here.
admin.site.register(Theme, admin.ModelAdmin)
admin.site.register(Settings, admin.ModelAdmin)
