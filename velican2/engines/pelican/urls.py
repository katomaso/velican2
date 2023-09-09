from django.urls import path
from . import views

app_name="pelican"
urlpatterns = [
    path("", views.SettingsList.as_view(), name="settings"),
    path("<int:id>/", views.SettingsDetail.as_view(), name="setting"),
    path("<int:id>/themes/", views.ThemeList.as_view(), name="themes"),
    path("<int:id>/import-article/", views.ImportArticle.as_view(), name="import-article"),
]
