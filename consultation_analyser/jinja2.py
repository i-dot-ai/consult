from compressor.contrib.jinja2ext import CompressorExtension
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from jinja2 import ChoiceLoader, Environment, PackageLoader, PrefixLoader


def reverse_with_query_kwargs(viewname, kwargs=None, query_kwargs=None):
    url = reverse(viewname, kwargs=kwargs)

    if query_kwargs:
        return f"{url}?{urlencode(query_kwargs)}"

    return url


def render_form(form, request):
    return render_to_string("form.html", context={"form": form}, request=request, using="django")


def datetime(datetime_object):
    tz = timezone.get_current_timezone()
    with_tz = datetime_object.astimezone(tz)
    return with_tz.strftime("%d %B %Y at %H:%M")


def environment(**options):
    current_loader = options["loader"]
    loader_with_govuk_frontend = ChoiceLoader(
        [
            current_loader,
            PrefixLoader({"govuk_frontend_jinja": PackageLoader("govuk_frontend_jinja")}),
        ]
    )
    options["loader"] = loader_with_govuk_frontend

    # bandit is disabled here else it complains that autoescape = False
    # because it's not clever enough to know what's in **options - this assert is doing
    # bandit's job
    assert options["autoescape"] is True

    env = Environment(**options, extensions=[CompressorExtension])  # nosec

    tags = {
        "static": static,
        "url": reverse_with_query_kwargs,
        "render_form": render_form,
        "datetime": datetime,
    }

    env.filters["intcomma"] = intcomma

    env.globals.update(tags)

    return env
