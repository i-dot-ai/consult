from django.urls import include, path
from magic_link import urls as magic_link_urls

from .views import consultations, pages, questions, responses, schema, sessions

urlpatterns = [
    path("", pages.home),
    path("how-it-works/", pages.how_it_works),
    path("schema/", schema.show),
    path("data-sharing/", pages.data_sharing),
    path("get-involved/", pages.get_involved),
    path("privacy/", pages.privacy),
    path("consultations/", consultations.show_all),
    path("consultations/<str:consultation_slug>/", consultations.show, name="consultation"),
    path("schema/<str:schema_name>.json", schema.raw_schema),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>/",
        questions.show,
        name="show_question",
    ),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/responses/<str:question_slug>/",
        responses.show,
        name="show_question_responses",
    ),
    path("batch-example/", pages.batch_example, name="batch_example"),
    # authentication
    path("sign-in/", sessions.new),
    path("sign-out/", sessions.destroy),
    path("magic-link/", include(magic_link_urls)),
    path("batch-example", pages.batch_example, name="batch_example"),
]
