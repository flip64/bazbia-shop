
from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    path("", views.home, name="root"),
    path("home/", views.home, name="home"),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
