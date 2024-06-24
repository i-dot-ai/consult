from dataclasses import dataclass

from django.http import HttpRequest
from django.urls import resolve
from django.urls.exceptions import Resolver404


@dataclass
class AppConfig:
    name: str
    path: str
    menu_items: list
    show_provisional_data_warning: bool = False


def app_config(request: HttpRequest):
    try:
        resolved_url = resolve(request.path)
    except Resolver404:
        return {"app_config": AppConfig(name="Consult", path="/", menu_items=[])}

    current_app = resolved_url.func.__module__.split(".")[1]

    if current_app == "support_console":
        app_config = AppConfig(
            name="Consult support console",
            path="/support/",
            menu_items=[
                {
                    "href": "/support/consultations/",
                    "text": "Consultations",
                    "active": request.path.startswith("/support/consultations"),
                },
                {
                    "href": "/support/users/",
                    "text": "Users",
                    "active": request.path.startswith("/support/users"),
                },
                {
                    "href": "/support/sign-out/",
                    "text": "Sign out",
                    "classes": "x-govuk-primary-navigation__item--right",
                },
            ],
        )
    else:
        if request.user.is_authenticated:
            menu_items = [
                {
                    "href": "/consultations/",
                    "text": "Your consultations",
                    "active": request.path.startswith("/consultations"),
                },
                {
                    "href": "/sign-out/",
                    "text": "Sign out",
                    "classes": "x-govuk-primary-navigation__item--right",
                },
            ]
        else:
            menu_items = [
                {
                    "href": "/how-it-works/",
                    "text": "How it works",
                    "active": request.path == "/how-it-works/",
                },
                {
                    "href": "/schema/",
                    "text": "Data schema",
                    "active": request.path == "/schema/",
                },
                {
                    "href": "/data-sharing/",
                    "text": "Data sharing",
                    "active": request.path == "/data-sharing/",
                },
                {
                    "href": "/get-involved/",
                    "text": "Get involved",
                    "active": request.path == "/get-involved/",
                },
                {
                    "href": "/sign-in/",
                    "text": "Sign in",
                    "active": request.path == "/sign-in/",
                    "classes": "x-govuk-primary-navigation__item--right",
                },
            ]

        show_provisional_data_warning = request.user.is_authenticated and request.path.startswith(
            "/consultations"
        )
        app_config = AppConfig(
            name="Consult",
            path="/",
            menu_items=menu_items,
            show_provisional_data_warning=show_provisional_data_warning,
        )

    return {"app_config": app_config}
