from jinja2 import Environment
from django.urls import reverse
from django.templatetags.static import static
from compressor.contrib.jinja2ext import CompressorExtension


def environment(**options):
    # bandit is disabled on following line else it complains that autoescape = False
    # because it's not clever enough to know what's in **options - this assert is doing
    # bandit's job
    assert options["autoescape"] is True
    env = Environment(**options, extensions=[CompressorExtension])  # nosec
    env.globals.update({"static": static, "url": reverse})
    return env
