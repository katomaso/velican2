from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError

from velican2.core import models as core

from . import logger


class AWS(models.Model):
    site = models.ForeignKey(core.Site, null=False, on_delete=models.CASCADE)
    cloudfront_id = models.CharField(max_length=32, null=True)
    bucket_id = models.CharField(max_length=128, null=True, validators=[validators.validate_slug,])

    __str__ = lambda self: str(self.site)

    class Meta:
        verbose_name = "AWS"
        verbose_name_plural = "AWS"

    def clean(self):
        if self.site.deployment != "aws":
            raise ValidationError(f"Site {self.site} does not deploy with AWS")

    def save(self, **kwargs):
        if not self.id:
            bucket = self.s3.Bucket(self.site.domain)
            logger.info("Creating a new bucket " + self.site.domain)
            bucket.create(
                ACL='private',
                CreateBucketConfiguration={
                    'LocationConstraint': 'eu-central-1'
                })
            self.bucket_id = self.site.domain
        return super().save(**kwargs)

    def refresh(self):
        pass

    def deploy(self):
        pass

    @property
    def bucket(self):
        return AWS.s3.Bucket(self.bucket_id)

    def delete(self, **kwargs):
        self.bucket.delete()
        return super().delete(**kwargs)