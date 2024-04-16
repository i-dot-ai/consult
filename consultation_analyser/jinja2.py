import jinja2
from compressor.contrib.jinja2ext import CompressorExtension
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.urls import reverse
from jinja2 import ChoiceLoader, Environment, PackageLoader, PrefixLoader


def render_form(form, request):
    return render_to_string("form.html", context={"form": form}, request=request, using="django")


def environment(**options):
    current_loader = options["loader"]
    loader_with_govuk_frontend = ChoiceLoader(
        [current_loader, PrefixLoader({"govuk_frontend_jinja": PackageLoader("govuk_frontend_jinja")})]
    )
    options["loader"] = loader_with_govuk_frontend

    # bandit is disabled here else it complains that autoescape = False
    # because it's not clever enough to know what's in **options - this assert is doing
    # bandit's job
    assert options["autoescape"] is True

    env = Environment(**options, extensions=[CompressorExtension])  # nosec

    tags = {"static": static, "url": reverse, "render_form": render_form}

    env.globals.update(tags)

    return env
