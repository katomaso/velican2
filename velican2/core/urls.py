from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('', views.index, name="index"),
    path("start/", views.Start.as_view(), name="start"),
    path("sites/", views.Sites.as_view(), name="sites"),
    path("sites/<str:site>/", views.Site.as_view(), name="site"),
    path("sites/<str:site>/edit.html", views.SiteEdit.as_view(), name="site-edit"),
    path("sites/<str:site>/publish.html", views.Publish.as_view(), name="publish"),
    path("sites/<str:site>/images.html", views.Images.as_view(), name="images"),
    path("sites/<str:site>/post/add.html", views.PostCreate.as_view(), name="post-add"),
    path("sites/<str:site>/post/<int:post>/edit.html", views.Post.as_view(), name="post"),
    path("sites/<str:site>/post/<int:post>/delete.html", views.PostDelete.as_view(), name="post-delete"),
    path("legal.html", views.render_static_page),
]
