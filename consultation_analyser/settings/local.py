from django.conf.global_settings import STORAGES

from consultation_analyser.settings.base import *  # noqa

INSTALLED_APPS.append("django_extensions")  # noqa F405
INSTALLED_APPS.append("pyflame")  # noqa F405

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.alerts.AlertsPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    "debug_toolbar.panels.profiling.ProfilingPanel",
    "pyflame.djdt.panel.FlamegraphPanel",
]

STORAGES["default"] = {  # noqa
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {
        "location": BASE_DIR / "tmp"  # noqa
    },
}
