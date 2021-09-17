import os

from django.core.cache import cache
from django.http import JsonResponse


def get_ticket(request):
    try:
        date = request.GET["date"].strftime(os.environ.get("DATE_FORMAT"))
        fly_from = request.GET["fly_from"]
        fly_to = request.GET["fly_to"]
    except KeyError as e:
        print(e)
        return JsonResponse({"message": "Not all required fields"}, status=400)

    ticket = cache.get(f"{date}_{fly_from}_{fly_to}")

    if not ticket:
        return JsonResponse({"message": "Ticket not found"}, status=404)

    return JsonResponse(
        {"data": ticket, "date": date, "fly_from": fly_from, "fly_to": fly_to},
        status=200,
    )
