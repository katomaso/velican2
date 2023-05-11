from django.contrib import admin
from .models import AWS

# Register your models here.
admin.site.register(AWS, admin.ModelAdmin)