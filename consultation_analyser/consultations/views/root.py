from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest

from .pages import home


@login_not_required
def root(request: HttpRequest):
    return home(request)
