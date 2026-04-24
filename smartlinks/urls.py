from django.urls import path

from . import views

app_name = "smartlinks"

urlpatterns = [
    path("", views.home, name="home"),
    path("me/", views.dashboard, name="dashboard"),
    path("s/<slug:slug>/", views.landing, name="landing"),
    path(
        "s/<slug:slug>/go/<slug:platform>/",
        views.go_platform,
        name="go_platform",
    ),
]
