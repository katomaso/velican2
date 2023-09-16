import boto3
import mimetypes

from . import logger
from .. import IDeployer
from datetime import datetime
from django.apps import AppConfig
from django.conf import settings

class AWS(AppConfig, IDeployer):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'velican2.deployers.aws'

    def is_available(self):
        return self.available

    def ready(self):
        self.available = None
        if not settings.AWS_KEY:
            logger.error("AWS deployer not available! No AWS credentials set via AWS_KEY and AWS_SECRET")
            self.available = False
            return
        self.s3 = boto3.resource('s3',
            aws_access_key_id=settings.AWS_KEY,
            aws_secret_access_key=settings.AWS_SECRET,
        )
        self.cloudfront = boto3.client('cloudfront')
        self.available = True

    def bucket(self, bucket_name):
        """Get or create S3 bucket for given site"""
        buckets = tuple(filter(lambda b: b.name == bucket_name, self.s3.buckets.all()))
        if len(buckets) == 0:
            bucket = self.s3.Bucket(bucket_name)
            logger.info("Creating a new bucket " + bucket_name)
            bucket.create(
                ACL='public-read',
                CreateBucketConfiguration={
                    'LocationConstraint': 'eu-central-1'
                })
            return bucket
        return buckets[0]

    def invalidate(self, aws, post=None):
        paths = ["/*", ]
        if post:
            paths = [
                "/index.html",
                aws.site.get_engine().get_post_url(aws.site, post, absolute=False),
            ]

        self.cloudfront.create_invalidation(
            DistributionId=aws.cloudfront_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths,
                },
                'CallerReference': self.site.domain + datetime.utcnow().strftime("%y%m%d%H%M"),
            }
        )


    def deploy(self, site, post=None, page=None, **kwargs):
        from velican2.core import models as core
        bucket = self.bucket(site.urn)
        root = site.get_engine().get_output_path(site)
        if post is not None:
            path = site.get_engine().get_post_output_path(site, post)
            logger.info(f"Uploading post {path}")
            bucket.upload_file(path, str(path.relative_to(root)).replace("\\", "/"), ExtraArgs={'ContentType': "text/html"})
            return
        if page is not None:
            path = site.get_engine().get_page_output_path(site, page)
            logger.info(f"Uploading page {path}")
            bucket.upload_file(path, str(path.relative_to(root)).replace("\\", "/"), ExtraArgs={'ContentType': "text/html"})
            return
        # get the last published so we push only newly updated files
        last_upload = core.Publish.objects.last_successful()
        logger.info(f"Uploading root {root}")
        for path in root.rglob("*"): # gives you relative path including the root path
            if path.is_dir():
                continue
            if not kwargs.get("force", False) and not kwargs.get("purge", False) and last_upload is not None:
                # skip files older than last successfull publish (only when not purge or force are specified)
                mtime = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
                if mtime > last_upload.finished:
                    logger.debug(f"Skipping {path.relative_to(root)} because its mtime precedes last sucessfull upload")
                    continue
            logger.info(f"Uploading {path.relative_to(root)}")
            bucket.upload_file(path, str(path.relative_to(root)).replace("\\", "/"), ExtraArgs={'ContentType': mimetypes.guess_type(path.name)[0]})

    def purge(self, site):
        bucket = self.bucket(site.urn)
        # TODO: not tested
        bucket.delete_objects(Delete={
            'Objects': [{'Key': remote_object} for remote_object in bucket.list_objects()],
            'Quiet': True
        })

    def delete(self, site, post=None, page=None):
        bucket = self.bucket(site.urn)
        root = site.get_engine().get_output_path(site)
        if post is not None:
            path = site.get_engine().get_post_output_path(site, post)
            logger.info(f"Deleting post {path.relative_to(root)}")
            bucket.delete_files(Delete={'Objects': [{'Key': str(path.relative_to(root))}]})
            return
        if page is not None:
            path = site.get_engine().get_page_output_path(site, page)
            logger.info(f"Deleting page {path.relative_to(root)}")
            bucket.delete_files(Delete={'Objects': [{'Key': str(path.relative_to(root))}]})
            return
        bucket.delete()