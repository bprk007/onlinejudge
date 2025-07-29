from django.urls import path
from submit.views import submit

urlpatterns = [
    path("", submit, name="submit"),
]