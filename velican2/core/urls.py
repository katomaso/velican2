from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path('', views.index, name="index"),
    path("start/", views.Start.as_view(), name="start"),
    path("sites/", views.Sites.as_view(), name="sites"),
    path("sites/<str:site>/", views.Site.as_view(), name="site"),
    path("sites/<str:site>/images/", views.Images.as_view(), name="images"),
    path("sites/<str:site>/post/add.html", views.PostCreate.as_view(), name="add_post"),
    path("sites/<str:site>/post/<int:post>/edit.html", views.Post.as_view(), name="post"),
    path("legal.html", views.render_static_page),
]
