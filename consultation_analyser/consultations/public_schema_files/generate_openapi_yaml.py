# This script generates an OpenAPI schema for data imports to the Consultation app.

from typing import Any, Dict, List, Optional, TypedDict, cast

import yaml
from django.db.models import (
    BooleanField,
    CharField,
    FloatField,
    ForeignKey,
    IntegerField,
    JSONField,
    ManyToManyField,
    TextField,
)

from consultation_analyser.consultations.models import (
    Answer,
    ConsultationOld,
    EvidenceRichMapping,
    ExecutionRun,
    Framework,
    QuestionOld,
    QuestionPart,
    SentimentMapping,
    ThemeMapping,
    ThemeOld,
)

FIELDS_TO_EXCLUDE = [
    "id",
    "created_at",
    "modified_at",
    "slug",
    "users",
    "is_theme_mapping_audited",
    "themefinder_respondent_id",
]  # These are either auto-generated or populated after import
MODELS_TO_INCLUDE = [
    ConsultationOld,
    QuestionOld,
    QuestionPart,
    Answer,
    ExecutionRun,
    Framework,
    ThemeOld,
    ThemeMapping,
    SentimentMapping,
    EvidenceRichMapping,
]


class OpenAPIInfo(TypedDict):
    title: str
    version: str
    description: str


class OpenAPIComponents(TypedDict):
    schemas: Dict[str, Any]


class OpenAPISchema(TypedDict):
    openapi: str
    info: OpenAPIInfo
    paths: Dict[str, Any]
    components: OpenAPIComponents


class SchemaFieldProperty(TypedDict, total=False):
    type: str
    format: Optional[str]
    maxLength: Optional[int]
    enum: List[str]  # Note: List type for enum values
    example: Optional[str]
    description: Optional[str]


class OpenAPISchemaGenerator:
    """
    Generate OpenAPI schema from Django models without Django Rest Framework.
    """

    def __init__(self, title: str, version: str, description: str = ""):
        self.title = title
        self.version = version
        self.description = description
        self.schema: OpenAPISchema = {
            "openapi": "3.0.3",
            "info": {"title": self.title, "version": self.version, "description": self.description},
            "paths": {},
            "components": {"schemas": {}},
        }

    def _get_field_type(self, field) -> Dict[str, Any]:
        """Map Django field types to OpenAPI types."""
        field_type = type(field)

        if field_type in (CharField, TextField):
            schema: SchemaFieldProperty = {"type": "string"}
            if hasattr(field, "max_length") and field.max_length:
                schema["maxLength"] = field.max_length
            if hasattr(field, "choices") and field.choices:
                schema["enum"] = [choice[0] for choice in field.choices]
            return cast(Dict[str, Any], schema)

        elif field_type == IntegerField:
            return {"type": "integer"}

        elif field_type == FloatField:
            return {"type": "number", "format": "float"}

        elif field_type == BooleanField:
            return {"type": "boolean"}

        elif field_type == ForeignKey:
            return {
                "type": "uuid",
                "$ref": f"#/components/schemas/{field.related_model.__name__}",
            }

        elif field_type == ManyToManyField:
            return {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{field.related_model.__name__}"},
            }

        elif field_type == JSONField:
            if field.has_default() and field.default is not None:
                default_value = field.default
                if isinstance(default_value, list):
                    return {
                        "type": "array",
                        "items": {"type": "object", "additionalProperties": True},
                        "description": "JSON array data",
                    }

                return {  # default is a dict
                    "type": "object",
                    "additionalProperties": True,
                    "description": "JSON object data",
                }
            return {  # no default
                "type": "object",
                "additionalProperties": True,
                "description": "JSON data",
            }

        else:
            return {"type": "string"}

    def generate_model_schema(self, model) -> Dict[str, Any]:
        """Generate schema for a single model."""
        properties = {}
        required = []

        for field in model._meta.fields:
            if field.name in FIELDS_TO_EXCLUDE:
                continue
            field_schema = self._get_field_type(field)

            if hasattr(field, "help_text") and field.help_text:
                field_schema["description"] = field.help_text

            if not field.null and not field.blank and not field.primary_key:
                required.append(field.name)

            properties[field.name] = field_schema

        for field in model._meta.many_to_many:
            if field.name in FIELDS_TO_EXCLUDE:
                continue
            properties[field.name] = self._get_field_type(field)

        schema = {"type": "object", "properties": properties}

        if required:
            schema["required"] = required

        return schema

    def add_model(self, model) -> None:
        """Add a model schema to the components/schemas section."""
        model_name = model.__name__
        self.schema["components"]["schemas"][model_name] = self.generate_model_schema(model)

    def add_all_models(self) -> None:
        for model in MODELS_TO_INCLUDE:
            self.add_model(model)

        # Add a custom import-specific Respondent model schema
        self.schema["components"]["schemas"]["Respondent"] = {
            "type": "object",
            "properties": {
                "id": {"type": "any"},  # We will override this in themefinder
            },
            "required": ["id"],
        }

    def write_to_file(self, filename: str) -> None:
        content = yaml.dump(self.schema, sort_keys=False)

        with open(filename, "w") as f:
            f.write(content)


def generate_openapi_yaml():
    generator = OpenAPISchemaGenerator(
        title="Consult",
        version="1.0.0",
        description="OpenAPI schema for the models in the Consultations app",
    )
    generator.add_all_models()
    generator.write_to_file(
        "consultation_analyser/consultations/public_schema_files/public_schema.yaml"
    )
