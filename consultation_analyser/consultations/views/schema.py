import json

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from pydantic import BaseModel

from consultation_analyser.consultations import public_schema

SCHEMA_DIR = settings.BASE_DIR / "consultation_analyser" / "consultations" / "public_schema_files"

SCHEMA_MAPPINGS = {
    "answer": f"{SCHEMA_DIR}/answer_schema.json",
    "consultation": f"{SCHEMA_DIR}/consultation_schema.json",
    "executionrun": f"{SCHEMA_DIR}/executionrun_schema.json",
    "framework": f"{SCHEMA_DIR}/framework_schema.json",
    "question": f"{SCHEMA_DIR}/question_schema.json",
    "questionpart": f"{SCHEMA_DIR}/questionpart_schema.json",
    "respondent": f"{SCHEMA_DIR}/respondent_schema.json",
    "sentimentmapping": f"{SCHEMA_DIR}/sentimentmapping_schema.json",
    "theme": f"{SCHEMA_DIR}/theme_schema.json",
    "thememapping": f"{SCHEMA_DIR}/thememapping_schema.json",
}


class RenderableSchema:
    def __init__(self, schema: BaseModel):
        self.schema = schema

    def name(self):
        return self.schema.__name__

    def description(self):
        return self.schema.__doc__

    def rows(self):
        return []


class RenderableModelSchema(RenderableSchema):
    def rows(self):
        output = []
        for field_name in self.schema.model_fields.keys():
            field = self.schema.model_fields[field_name]

            field_details = {
                "name": field_name,
                "description": field.description,
                "datatype": field.annotation.__name__,
            }

            output.append(field_details)

        return output


class RenderableEnumSchema(RenderableSchema):
    def values(self):
        return [entry.value for entry in list(self.schema)]


def pretty_format_json(json_string: str) -> str:
    return json.dumps(json.loads(json_string), indent=2)


def raw_schema(request: HttpRequest, schema_name: str) -> HttpResponse:
    # this is here so we don't use untrusted input to traverse the filesystem
    if not (schema_to_serve := SCHEMA_MAPPINGS.get(schema_name)):
        raise Http404("Schema does not exist")

    return HttpResponse(open(schema_to_serve, "r").read(), content_type="application/json")


def show(request: HttpRequest) -> HttpResponse:
    json_schemas = {
        "questionpart": open(SCHEMA_MAPPINGS["questionpart"]).read(),
        "answer": open(SCHEMA_MAPPINGS["answer"]).read(),
    }

    entity_schemas = [
        RenderableModelSchema(public_schema.Consultation),
        RenderableModelSchema(public_schema.Question),
        RenderableEnumSchema(public_schema.Type),
        RenderableModelSchema(public_schema.QuestionPart),
        RenderableModelSchema(public_schema.Respondent),
        RenderableModelSchema(public_schema.Answer),
    ]

    return render(
        request,
        "consultations/schema.html",
        {
            "json_schemas": json_schemas,
            # add json_examples
            "entity_schemas": entity_schemas,
        },
    )
