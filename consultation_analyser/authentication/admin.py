from django.contrib import admin
from django.contrib.auth.models import Group

# leave this out until we know what we’re doing with Groups etc
admin.site.unregister(Group)
