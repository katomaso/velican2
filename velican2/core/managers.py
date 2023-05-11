from django.db import models

class PublishManager(models.Manager):

    def last_successful(self):
        try:
            return self.get_queryset().filter(success=True).order_by('-finished')[0:1].get()
        except self.model.DoesNotExist:
            return None
