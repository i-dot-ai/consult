from rest_framework import serializers

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ["name", "description", "key"]


class ResponseAnnotationThemeSerializer(serializers.ModelSerializer):
    theme = ThemeSerializer()

    class Meta:
        model = ResponseAnnotationTheme
        fields = ["theme", "is_original_ai_assignment", "assigned_by"]


class ResponseAnnotationSerializer(serializers.ModelSerializer):
    themes = ResponseAnnotationThemeSerializer(source="responseannotationtheme_set", many=True)

    class Meta:
        model = ResponseAnnotation
        fields = [
            "themes",
            "sentiment",
            "evidence_rich",
            "human_reviewed",
            "reviewed_by",
            "reviewed_at",
        ]


class ResponseSerializer(serializers.ModelSerializer):
    annotation = ResponseAnnotationSerializer()

    class Meta:
        model = Response
        fields = [
            "id",
            "free_text",
            "chosen_options",
            "annotation",
        ]


class ConsultationSerializer(serializers.HyperlinkedModelSerializer):
    questions = serializers.PrimaryKeyRelatedField(
        source="question_set",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Consultation
        fields = ["id", "title", "slug", "questions"]


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "slug",
            "number",
            "has_free_text",
            "has_multiple_choice",
            "multiple_choice_options",
        ]
