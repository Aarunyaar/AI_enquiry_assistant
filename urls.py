from django.urls import path
from .views import home, chat_api

urlpatterns = [
    path("", home),
    path("chat/", chat_api),
]