from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views import generic
from django import forms

from . import logger
from .models import Settings, Theme, ThemeSettings
from .forms import SettingsForm
from velican2.core.views import SiteMixin


class SettingsList(LoginRequiredMixin, generic.ListView):
    model = Settings

    def get_queryset(self) -> QuerySet[Any]:
        return Settings.objects.filter(site__admin=self.request.user)


class SettingsDetail(SiteMixin, generic.UpdateView):
    model = Settings
    form_class = SettingsForm
    template_name = "pelican/settings_detail.html"

    def get_object(self, queryset: QuerySet[Any] = None) -> Settings:
        return Settings.objects.get(site=self.site)
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(**kwargs,
                                        themes=Theme.objects.filter(image__isnull=False).exclude(image=""))


class ImportArticle(SiteMixin, generic.View):
    model = Settings

    def get_object(self, queryset: QuerySet[Any] = None) -> Settings:
        return Settings.objects.get(site=self.site)

    def post(self, request, site:str):
        pelican = self.get_object()
        for file in request.FILES.getlist('posts'):
            pelican.import_article(file, request.user)
            messages.info(request, " ".join((_("File"), file.name, _("imported sucessfully"))))
        # except Exception as e:
        #     logger.error(type(e))
        #     logger.error(e)
        #     messages.error(request, _("Could not process file"))
        return redirect(request.headers['Referer'])


class ThemeList(LoginRequiredMixin, generic.ListView):
    template_name = "pelican/theme_list.html"
    model = Theme

    class Form(forms.Form):
        theme_id = forms.CharField(required=True)
        settings = forms.CharField(required=False, widget=forms.Textarea)

        def clean_theme_id(self, value):
            try:
                return Theme.objects.get(pk=value)
            except Exception as e:
                raise forms.ValidationError(str(e))

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        logger.debug(f"Context: {kwargs}")
        pelican = Settings.objects.get(id=self.kwargs['id'])
        kwargs.update(
            pelican=pelican,
            settings={theme_id: settings for (theme_id, settings) in ThemeSettings.objects.filter(
                pelican=pelican).values_list('theme_id', 'settings')}
        )
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.Form(request.POST)
        if form.is_valid():
            request.user.site
            return HttpResponseRedirect()
        self.object_list=self.get_queryset()
        return self.render_to_response(
            self.get_context_data(form=form))
