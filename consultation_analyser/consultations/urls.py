from django.urls import path, include

from .views import consultations, pages, questions, responses, schema, sessions
from magic_link import urls as magic_link_urls

urlpatterns = [
    path("", pages.home),
    path("privacy", pages.privacy),
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
        responses.show,
        name="show_question_responses",
    ),
    # authentication
    path("sign-in/", sessions.new),
    path("sign-out/", sessions.destroy),
    path("magic-link/", include(magic_link_urls)),
    path("batch-example", pages.batch_example, name="batch_example"),
]
