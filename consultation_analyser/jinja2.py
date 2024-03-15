from jinja2 import Environment, ChoiceLoader, PrefixLoader, PackageLoader
from django.urls import reverse
from django.templatetags.static import static
from compressor.contrib.jinja2ext import CompressorExtension


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
    env.globals.update({"static": static, "url": reverse})
    return env
