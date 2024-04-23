from dataclasses import dataclass

import waffle
from django.http import HttpRequest


@dataclass
class AppConfig:
    name: str
    path: str
    menu_items: list


def app_config(request: HttpRequest):
    if request.current_app == "support_console":
        app_config = AppConfig(
            name="Consultation analyser support console",
            path="/support/",
            menu_items=[
                {
                    "href": "/support/consultations/",
                    "text": "Consultations",
                },
                {
                    "href": "/support/sign-out/",
                    "text": "Sign out",
                },
            ],
        )
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
        ]

        if waffle.switch_is_active("FRONTEND_USER_LOGIN"):
            if request.user.is_authenticated:
                menu_items.append(
                    {
                        "href": "/sign-out/",
                        "text": "Sign out",
                    }
                )
            else:
                menu_items.append(
                    {
                        "href": "/sign-in/",
                        "text": "Sign in",
                        "active": request.path == "/sign-in/",
                    }
                )

        app_config = AppConfig(name="Consultation analyser", path="/", menu_items=menu_items)

    return {"app_config": app_config}
