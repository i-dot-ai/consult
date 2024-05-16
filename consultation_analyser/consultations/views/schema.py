import json

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from .. import public_schema
from ..decorators.renderable_schema import RenderableSchema


def pretty_format_json(json_string: str) -> str:
    return json.dumps(json.loads(json_string), indent=2)


SCHEMA_DIR = settings.BASE_DIR / "consultation_analyser" / "consultations" / "public_schema"


def raw_schema(request: HttpRequest, schema_name: str):
    mappings = {
        "consultation_schema": f"{SCHEMA_DIR}/consultation_schema.json",
        "consultation_response_schema": f"{SCHEMA_DIR}/consultation_response_schema.json",
        "consultation_with_responses_schema": f"{SCHEMA_DIR}/consultation_with_responses_schema.json",
    }

    # this is here so we don't use untrusted input to traverse the filesystem
    if not (schema_to_serve := mappings.get(schema_name)):
        raise Http404("Schema does not exist")

    return HttpResponse(open(schema_to_serve, "r").read(), content_type="application/json")


def show(request: HttpRequest):
    json_schemas = {
        "consultation": pretty_format_json(open(f"{SCHEMA_DIR}/consultation_schema.json").read()),
        "consultation_response": pretty_format_json(open(f"{SCHEMA_DIR}/consultation_response_schema.json").read()),
        "consultation_with_responses": pretty_format_json(
            open(f"{SCHEMA_DIR}/consultation_with_responses_schema.json").read()
        ),
    }

    json_examples = {
        "consultation": pretty_format_json(open(f"{SCHEMA_DIR}/consultation_example.json").read()),
        "consultation_response": pretty_format_json(open(f"{SCHEMA_DIR}/consultation_response_example.json").read()),
        "consultation_with_responses": pretty_format_json(
            open(f"{SCHEMA_DIR}/consultation_with_responses_example.json").read()
        ),
    }

    entity_schemas = [
        RenderableSchema(public_schema.Consultation),
        RenderableSchema(public_schema.Section),
        RenderableSchema(public_schema.Question),
        RenderableSchema(public_schema.Answer),
        RenderableSchema(public_schema.MultipleChoice),
        RenderableSchema(public_schema.MultipleChoiceItem),
        RenderableSchema(public_schema.ConsultationResponse),
    ]

    return render(
        request,
        "schema.html",
        {"json_schemas": json_schemas, "json_examples": json_examples, "entity_schemas": entity_schemas},
    )
