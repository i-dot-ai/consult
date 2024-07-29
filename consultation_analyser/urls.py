"""
URL configuration for consultation_analyser project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from consultation_analyser.consultations import urls
from consultation_analyser.error_pages import views as error_views
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.support_console import urls as support_console_urls

handler404 = error_views.error_404
handler500 = error_views.error_500

adminurlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns = [
    path("", include(urls)),
    path("support/", include(support_console_urls)),
]

if HostingEnvironment.is_local():
    urlpatterns = urlpatterns + adminurlpatterns
