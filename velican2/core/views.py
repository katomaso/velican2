import io
import json

from io import BytesIO
from datetime import date
from typing import Any, Dict, Optional
from django import http
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse
from django.views import generic as generic_views
from django.views.generic import edit as edit_views 
from django.utils.translation import gettext as _
from pathlib import Path

from markdownx import utils as image_utils
from martor.utils import LazyEncoder
from velican2.engines import pelican

from . import models
from . import forms
from . import logger


def index(request: http.HttpRequest):
    return render(request, "index.html")


class Start(LoginRequiredMixin, generic_views.FormView):
    form_class = forms.StartForm
    template_name = "start.html"

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(admin=self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:add_post", site=self.object.urn)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(
            urn=settings.DOMAIN,
            pelican_themes=pelican.models.Theme.objects.exclude(image__isnull=True).exclude(image=""),
            **kwargs)


class SiteMixin:
    def dispatch(self, request, site:str, *args, **kwargs):
        if request.user.is_anonymous:
            return redirect("account_login")
        try:
            self.site = models.Site.objects.filter(admin=request.user, urn=site).get()
        except models.Site.DoesNotExist:
            messages.info(request, _("Site required"))
            return redirect("core:start")
        return super().dispatch(request, *args, site=site, **kwargs)
    
    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(*args, **kwargs, site=self.site)


class PostMixin:
    def dispatch(self, request, post:int, *args, **kwargs):
        try:
            self.post = models.Post.objects.get(pk=post)
            if self.post.site != self.site:
               logger.error(f"User {request.user} trying to access else's post {post}")
               raise models.Site.DoesNotExist()
        except models.Site.DoesNotExist:
            messages.info(request, _("Post does not exists"))
            return redirect("core:start")
        return super().dispatch(request, *args, post=post, **kwargs)
    
    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(*args, **kwargs, site=self.site)


class Site(SiteMixin, generic_views.DetailView):
    template_name = "site.html"

    def get_object(self):
        return self.site
    
    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            *args,
            posts = models.Post.objects.filter(site=self.site),
            **kwargs)


class Sites(LoginRequiredMixin, generic_views.ListView):
    template_name = "sites.html"

    def get_queryset(self):
        return models.Site.objects.filter(admin=self.request.user)

    def get(self, request):
        sites_count = models.Site.objects.filter(admin=request.user).count()
        if sites_count == 0:
            return redirect('core:start')
        if sites_count == 1:
            return redirect('core:site', models.Site.objects.get(admin=request.user).urn)
        return super().get(request)


def append_to_name(path: Path, appendix: str, sep="-") -> Path:
    return path.with_stem(path.stem + sep + appendix)


class PostCreate(SiteMixin, edit_views.CreateView):
    form_class = forms.PostCreateForm
    template_name = "post-add.html"

    def get_initial(self):
        return {'lang': self.site.lang, 'site': self.site, 'author': self.request.user}

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        form.cleaned_data['site'] = self.site
        form.cleaned_data['author'] = self.request.user
        self.object = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:post", kwargs=dict(site=self.site.urn, post=self.object.id))


class Post(SiteMixin, edit_views.UpdateView):
    form_class = forms.PostForm
    template_name = "post.html"
    image_upload_field = 'markdown-image-upload'
    image_types = [
        'image/png', 'image/jpg',
        'image/jpeg', 'image/pjpeg', 'image/gif'
    ]
    image_format = {
        'image/png': "png",
        'image/jpg': "jpeg",
        'image/jpeg': "jpeg",
        'image/pjpeg': "jpeg",
        'image/gif': "gif",
    }

    def get_object(self) -> models.Post:
        return self.post

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        if self.image_upload_field in request.FILES:
            return self.upload_image(request)
        return super().post(request, *args, **kwargs)

    def upload_image(self, request):
        image_file = request.FILES[self.image_upload_field]
        image_name = append_to_name(Path(image_file.name),  date.today().isoformat())
        upload_dir = self.site.get_media_dir()

        if not upload_dir.exists():
            upload_dir.mkdir()

        if image_file.content_type not in self.image_types:
            data = json.dumps({
                'status': 405,
                'error': _('Bad image format.')
            }, cls=LazyEncoder)
            return HttpResponse(
                data, content_type='application/json', status=405)

        if image_file.size > settings.MAX_IMAGE_UPLOAD_SIZE:
            data = json.dumps({
                'status': 405,
                'error': _('Maximum image size exceeded') + str(settings.MAX_IMAGE_UPLOAD_SIZE / (1024 * 1024)) + "MB"
            }, cls=LazyEncoder)
            return HttpResponse(
                data, content_type='application/json', status=405)

        image = image_utils.scale_and_crop(image_file, settings.MAX_IMAGE_SIZE)
        image_buffer = BytesIO()
        image.save(image_buffer, format=self.image_format[image_file.content_type])
        media_path = default_storage.save(upload_dir / image_name, ContentFile(image_buffer.getvalue()))

        # image_mobile = image_utils.scale_and_crop(image_file, settings.MAX_IMAGE_SIZE_MOBILE, crop=True)
        # image_mobile.seek(0)
        # media_path = default_storage.save(upload_dir / append_to_name(image_name, "mobile"), ContentFile(image_mobile.tobytes()))

        return JsonResponse({'status': 200, 'link': settings.MEDIA_URL + media_path, 'name': str(image_name)})


class Images(SiteMixin, generic_views.View):
    def get(self, request, site):
        images_dir = self.site.get_media_dir()
        images_url = [{
            "link": f"{settings.MEDIA_URL}{self.site.urn}/{d.name}",
            "name": d.name
            } for d in images_dir.iterdir()]
        return JsonResponse(images_url, safe=False)


def publish(request: http.HttpRequest, site: str):
    def as_bool(value: str):
        return value.lower() in ("1", "true", "yes")

    return get_object_or_404(models.Site, urn=site).publish(
        request.user,
        force=as_bool(request.GET.get("force", "False")),
        purge=as_bool(request.GET.get("purge", "False")),
    )

def render_static_page(request: http.HttpRequest):
    return render(request, Path(request.path).name)
