from django.contrib import admin
from waffle.models import Flag, Sample

admin.site.site_header = "Consultation analyser admin panel"

# we aren't using these features of django-waffle yet
admin.site.unregister(Flag)
admin.site.unregister(Sample)
