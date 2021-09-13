from django.urls import path

from booking.views import get_ticket

urlpatterns = [
    path("", get_ticket),
]
