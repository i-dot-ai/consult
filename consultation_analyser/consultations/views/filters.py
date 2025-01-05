from django.http import HttpRequest


def get_applied_filters(request: HttpRequest) -> dict[str, str]:
    return {
        "keyword": request.GET.get("keyword", ""),
        "theme": request.GET.get("theme", "All"),
    }
