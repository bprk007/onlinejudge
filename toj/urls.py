"""
URL configuration for toj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from submit import views
from django.shortcuts import redirect
from account.views import register_user,login_user,logout_user


urlpatterns = [
    path('', lambda request: redirect('login')),
    path('admin/', admin.site.urls),
    path('auth/login/', login_user,name='login'),
    path('auth/register',register_user,name='register'),
    # Your logout path (optional)
    #path('auth/logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('auth/', include('account.urls')),  # custom auth if any
    path("submit/", include("submit.urls")),
    path("problems/", views.problem_list, name="problem_list"),
    path("problems/<slug:slug>/", views.submit, name="submit_with_problem"),
    path("problems/<slug:slug>/", views.problem_detail, name="problem_detail"),
    path("home/",include('home.urls'))
]
