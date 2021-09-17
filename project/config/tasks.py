import os
import time

from celery import shared_task

from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
from django.core.cache import cache

FIRST_CITIES = ['ALA', 'ALA', 'ALA', 'TSE', 'TSE']
SECOND_CITIES = ['TSE', 'MOW', 'CIT', 'MOW', 'LED']

BOOKING_URL = "https://api.skypicker.com/flights"
BOOKING_CHECK_URL = "https://booking-api.skypicker.com/api/v0.1/check_flights"


@shared_task
def get_tickets():
    today = datetime.today()
    date_from = today.strftime(os.environ.get("DATE_FORMAT"))
    date_to = (today + relativedelta(months=1)).strftime("%d/%m/%Y")

    for first, second in zip(FIRST_CITIES, SECOND_CITIES):
        ticket_by_direction(first, second, date_from, date_to)
        ticket_by_direction(second, first, date_from, date_to)


def ticket_by_direction(
    fly_from, fly_to, date_from, date_to, adults=1, children=0, infants=0
):
    number_of_person = adults + children + infants
    response_parameters = {
        "fly_from": fly_from,
        "fly_to": fly_to,
        "date_from": date_from,
        "date_to": date_to,
        "adults": adults,
        "children": children,
        "infants": infants,
        "partner": os.environ.get("PARTNER"),
        "curr": "KZT",
    }
    response = requests.get(BOOKING_URL, params=response_parameters)
    if response.status_code != 200:
        return response.text, response.status_code
    tickets = response.json()["data"]
    for ticket in tickets:
        ticket_date = datetime.utcfromtimestamp(ticket["dTimeUTC"]).strftime(os.environ.get("DATE_FORMAT"))
        key = f"{ticket_date}_{fly_from}_{fly_to}"
        if cache.get(key) is None:
            if check_ticket(ticket["booking_token"], number_of_person) != 0:
                break
            value = {"price": ticket["price"], "booking_token": ticket["booking_token"]}
            seconds, minutes, hours = 60, 60, 24
            cache.set(key, value, (seconds * minutes * hours) + 1)


def check_ticket(booking_token, pnum):
    retry_timer = 5
    retry_limit = 300
    response_parameters = {
        "booking_token": booking_token,
        "bnum": 1,
        "pnum": pnum,
        "currency": "KZT",
    }

    response = requests.get(BOOKING_CHECK_URL, params=response_parameters)
    if response.status_code != 200:
        return response.text, response.status_code
    check_result = response.json()
    is_checked = check_result["flights_checked"]
    is_invalid = check_result["flights_invalid"]

    while not is_checked and retry_timer < retry_limit:
        time.sleep(retry_timer)
        response = requests.get(BOOKING_CHECK_URL, params=response_parameters)
        if response.status_code != 200:
            return response.text, response.status_code
        is_checked = response.json()["flights_checked"]
        is_invalid = response.json()["flights_invalid"]
        retry_timer += 10
    is_price_changed = check_result["price_change"]

    if is_invalid:
        return 1

    elif is_price_changed:
        return 1
    return 0
