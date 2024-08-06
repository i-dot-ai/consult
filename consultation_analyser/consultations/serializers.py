from rest_framework import serializers
from drf_jsonschema_serializer.fields import JSONSchemaField



# Very basic serializer for testing
class ExampleSerializer(serializers.Serializer):
	json_data = JSONSchemaField(schema={"type": "object"})
