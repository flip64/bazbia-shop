from django.urls import path
from customers.api.views import *


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path('send-otp/', SendOtpView.as_view(), name='send-otp'),
    path('verify-otp/',VerifyOtpView.as_view(), name='verify-otp'),
    path('current/me/',CurrentUserView.as_view(), name='CurrentUser'),
    path("login/", LoginView.as_view(), name="login"),


]
