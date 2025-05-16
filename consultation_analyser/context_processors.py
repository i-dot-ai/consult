from dataclasses import dataclass

from django.conf import settings
from django.http import HttpRequest
from django.urls import resolve
from django.urls.exceptions import Resolver404


@dataclass
class AppConfig:
    name: str
    path: str
    menu_items: list


@dataclass
class Version:
    sha: str

    def version_string(self):
        if self.sha:
            return f"Version: {self.sha[:8]}"
        else:
            # Jinja2 will not print this, which is what we want
            return ""

    def url(self):
        if self.sha:
            return f"https://github.com/i-dot-ai/consultation-analyser/commit/{self.sha}"


def version(request: HttpRequest):
    return {"version": Version(sha=settings.GIT_SHA)}


def app_config(request: HttpRequest):
    try:
        resolved_url = resolve(request.path)
    except Resolver404:
        return {"app_config": AppConfig(name="Consult", path="/", menu_items=[])}

    current_app = resolved_url.func.__module__.split(".")[1]

    if request.user.is_authenticated:
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
                        "href": "/support/consultations/import-summary/",
                        "text": "Import",
                        "active": request.path.startswith("/support/consultations/import-summary"),
                    },
                    {
                        "href": "/support/sign-out/",
                        "text": "Sign out",
                        "classes": "x-govuk-primary-navigation__item--right",
                    },
                ],
            )
        else:  # regular (non-support console) app
            menu_items = []
            if request.user.is_staff:
                menu_items = [
                    {
                        "href": "/support/",
                        "text": "Support",
                    },
                ]

            menu_items.extend(
                [
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
            )

            app_config = AppConfig(
                name="Consult",
                path="/",
                menu_items=menu_items,
            )

    else:  # non-authenticated user
        app_config = AppConfig(
            name="Consult",
            path="/",
            menu_items=[
                {
                    "href": "/how-it-works/",
                    "text": "How it works",
                    "active": request.path == "/how-it-works/",
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
            ],
        )

    return {"app_config": app_config}
