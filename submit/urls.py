from django.urls import path
from submit.views import submit
from account.views import register_user,login_user,logout_user
urlpatterns = [
    path("", submit, name="submit"),
    path('logout/',logout_user, name='logout')
]