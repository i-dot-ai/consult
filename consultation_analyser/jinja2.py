from urllib.parse import urlencode

from compressor.contrib.jinja2ext import CompressorExtension
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
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


def is_in(value, selected):
    lst = [s["id"] for s in selected]
    return str(value) in lst


def replace_query_param(request, key, value):
    query = request.GET.copy()
    query.pop(key, None)
    query[key] = value
    return query.urlencode()


def remove_query_param(request, key, value):
    print("DEBUGGING 🐛")
    query = request.GET.copy()
    query_dict = {k: v for k, v in query.lists()}
    query_dict[key].remove(value)
    print(f"query after: {query_dict}")
    print(urlencode(query_dict))
    return urlencode(query_dict, doseq=True)


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
        "is_in": is_in,
        "replace_query_param": replace_query_param,
        "remove_query_param": remove_query_param,
    }

    env.filters["intcomma"] = intcomma

    env.globals.update(tags)

    return env
