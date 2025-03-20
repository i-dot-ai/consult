import json
from typing import Any, Dict, List, Optional, TypedDict

import yaml
from django.apps import apps
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    ForeignKey,
    IntegerField,
    JSONField,
    ManyToManyField,
    TextField,
)


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
            schema = {"type": "string"}
            if hasattr(field, "max_length") and field.max_length:
                schema["maxLength"] = field.max_length
            return schema

        elif field_type == IntegerField:
            return {"type": "integer"}

        elif field_type == FloatField:
            return {"type": "number", "format": "float"}

        elif field_type == BooleanField:
            return {"type": "boolean"}

        elif field_type == DateTimeField:
            return {"type": "string", "format": "date-time"}

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
            field_schema = self._get_field_type(field)

            if hasattr(field, "help_text") and field.help_text:
                field_schema["description"] = field.help_text

            if not field.null and not field.blank and not field.primary_key:
                required.append(field.name)

            properties[field.name] = field_schema

        for field in model._meta.many_to_many:
            properties[field.name] = self._get_field_type(field)

        schema = {"type": "object", "properties": properties}

        if required:
            schema["required"] = required

        return schema

    def add_model(self, model) -> None:
        """Add a model schema to the components/schemas section."""
        model_name = model.__name__
        self.schema["components"]["schemas"][model_name] = self.generate_model_schema(model)

    def add_all_models(self, app_labels: Optional[List[str]] = None) -> None:
        """Add all models from specified apps or all installed apps."""
        if app_labels:
            models = [
                model
                for app_label in app_labels
                for model in apps.get_app_config(app_label).get_models()
            ]
        else:
            models = apps.get_models()

        for model in models:
            self.add_model(model)

    def add_path(self, path: str, methods: Dict[str, Dict[str, Any]]) -> None:
        """Add a path to the OpenAPI schema."""
        self.schema["paths"][path] = methods

    def generate_yaml(self) -> str:
        """Generate YAML representation of the schema."""
        return yaml.dump(self.schema, sort_keys=False)

    def generate_json(self) -> str:
        """Generate JSON representation of the schema."""
        return json.dumps(self.schema, indent=2)

    def write_to_file(self, filename: str, format: str = "yaml") -> None:
        """Write the schema to a file."""
        if format.lower() == "yaml":
            content = self.generate_yaml()
        else:
            content = self.generate_json()

        with open(filename, "w") as f:
            f.write(content)


def generate_openapi_yaml():
    generator = OpenAPISchemaGenerator(
        title="Consult",
        version="1.0.0",
        description="OpenAPI schema for the models in the Consultations app",
    )
    generator.add_all_models(["consultations"])
    generator.write_to_file(
        "consultation_analyser/consultations/public_schema/public_schema.yaml", format="yaml"
    )
