from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("auth/login/", views.login, name="login"),
    path("jobs/", views.jobs, name="jobs"),
]

