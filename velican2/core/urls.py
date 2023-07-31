from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('', views.index),
    path("start/", views.Start.as_view(), name="start"),
    path("sites/", views.Sites.as_view(), name="sites"),
    path("sites/<str:site>/", views.Site.as_view(), name="site"),
    path("sites/<str:site>/post/add.html", views.Post.as_view(), name="add_post"),
    path('domains/', views.domains),
    path("legal.html", views.page),
]
