from django.urls import path

from consultation_analyser.hosting_environment import HostingEnvironment

from .views import consultations, pages, questions, schema

development_environments = HostingEnvironment.is_local() or HostingEnvironment.is_test() or HostingEnvironment.is_dev()


urlpatterns = [
    path("", pages.home),
    path("consultations", consultations.show_questions),
    path("schema", schema.show),
    path("schema/<str:schema_name>.json", schema.raw_schema),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        questions.show,
        name="show_question",
    ),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/responses/<str:question_slug>",
        questions.show_responses,
        name="show_responses",
    ),
    path(
        "consultations/<str:consultation_slug>",
        consultations.show_consultation,
        name="show_consultation",
    ),
]

development_urlpatterns = [
    path("consultation-example", consultations.create_dummy_data, name="consultation_example"),
    path("batch-example", pages.batch_example, name="batch_example"),
]


if development_environments:
    urlpatterns = urlpatterns + development_urlpatterns
