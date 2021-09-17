from django.urls import path

from .views import get_ticket

urlpatterns = [
    path("", get_ticket),
]
