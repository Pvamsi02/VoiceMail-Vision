from django.urls import include
from django.urls import re_path as url
from . import views
app_name = "homepage"

urlpatterns = [
    url(r"^$", views.introduction_view, name="introduction"),
    url(r"^login/$", views.login_view, name="login"),
    url(r"^compose/$", views.compose_view, name="compose"),
    url(r"^inbox/$", views.inbox_view, name="inbox"),
    url(r"^sent/$", views.sent_view, name="sent"),
    url(r"^trash/$", views.trash_view, name="trash"),
    url(r"^options/$", views.options_view, name="options"),
    url(r"^logout/$", views.logout_view, name="logout"),
]
