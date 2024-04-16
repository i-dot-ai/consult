from django.contrib import admin
from waffle.models import Flag, Sample
from magic_link.models import MagicLink, MagicLinkUse

admin.site.site_header = "Consultation analyser admin panel"

# we aren't using these features of django-waffle yet
admin.site.unregister(Flag)
admin.site.unregister(Sample)

admin.site.unregister(MagicLink)
admin.site.unregister(MagicLinkUse)
