from django.db.models import Count, QuerySet
from django.http import HttpRequest

from .. import models


def get_applied_filters(request: HttpRequest) -> dict[str, str]:
    return {
        "keyword": request.GET.get("keyword", ""),
        "theme": request.GET.get("theme", "All"),
    }

