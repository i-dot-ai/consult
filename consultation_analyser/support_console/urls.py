from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

from .views import consultations, consultations_users, pages, questions, users

urlpatterns = [
    path("", lambda request: redirect("/support/consultations/"), name="support"),
    path("sign-out/", pages.sign_out, name="support_sign_out"),
    path("users/", users.index, name="users"),
    path("users/new/", users.new, name="new_user"),
    path("users/<int:user_id>/", users.show, name="user"),
    path("consultations/", consultations.index, name="support_consultations"),
    path("consultations/<uuid:consultation_id>/", consultations.show, name="support_consultation"),
    path(
        "consultations/<uuid:consultation_id>/delete/",
        consultations.delete,
        name="delete_consultation",
    ),
    path(
        "consultations/<uuid:consultation_id>/users/<int:user_id>/remove/",
        consultations_users.delete,
        name="remove_user",
    ),
    path(
        "consultations/<uuid:consultation_id>/users/new/",
        consultations_users.new,
        name="add_user",
    ),
    path(
        "consultations/import-xlsx/",
        consultations.import_consultations_xlsx,
        name="import_consultations_xlsx",
    ),
    path(
        "consultations/<uuid:consultation_id>/export/",
        consultations.export_consultation_theme_audit,
        name="export_consultation_theme_audit",
    ),
    path(
        "consultations/<uuid:consultation_id>/export-urls/",
        consultations.export_urls_for_consultation,
        name="export_urls_for_consultation",
    ),
    path(
        "consultations/<uuid:consultation_id>/questions/<uuid:question_id>/delete/",
        questions.delete,
        name="delete_question",
    ),
    path("admin/", admin.site.urls),
    path("django-rq/", include("django_rq.urls")),
    path(
        "consultations/import-inputs/",
        consultations.import_consultation_inputs,
        name="import_inputs",
    ),
    path(
        "consultations/import-respondents/",
        consultations.import_consultation_respondents,
        name="import_respondents",
    ),
]
