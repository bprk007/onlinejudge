from django.urls import path
from home.views import home
from account.views import register_user,login_user,logout_user
urlpatterns = [
    path("", home, name="home"),
    path('logout/',logout_user, name='logout'),
    
]