
from django.urls import path
from . import views

app_name = "travel_assistant"

urlpatterns = [
    path("chat/", views.chat_api, name="chat"),
]
