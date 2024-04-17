from dataclasses import dataclass

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
            path="/support",
            menu_items=[
                {
                    "href": "/support/sign-out",
                    "text": "Sign out",
                }
            ],
        )
    else:
        app_config = AppConfig(
            name="Consultation analyser",
            path="/",
            menu_items=[
                {
                    "href": "/schema",
                    "text": "Data schema",
                    "active": request.path == "/schema",
                }
            ],
        )

    return {"app_config": app_config}
