from django.urls import path
from . import views

app_name="pelican"
urlpatterns = [
    path("", views.SettingsList.as_view(), name="settings"),
    path("<str:site>/", views.SettingsDetail.as_view(), name="setting"),
    path("<str:site>/themes/", views.ThemeList.as_view(), name="themes"),
    path("<str:site>/import-article/", views.ImportArticle.as_view(), name="import-article"),
]
