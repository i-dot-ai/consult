from rest_framework import serializers


class DemographicOptionsSerializer(serializers.Serializer):
    demographic_options = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField())
    )