from django.db import models



# Create your models here.
class Settings(models.Model):

    @property
    def admin_url(self):
        return