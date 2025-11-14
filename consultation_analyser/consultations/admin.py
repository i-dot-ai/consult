import json

from django.contrib import admin, messages
from django_rq import get_queue
from simple_history.admin import SimpleHistoryAdmin

from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml_job
from consultation_analyser.consultations.models import (
    CandidateTheme,
    Consultation,
    CrossCuttingTheme,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from consultation_analyser.run_themefinder import (
    sync_detail_detection,
    sync_theme_mapping,
    theme_identifier,
)
from consultation_analyser.support_console.ingest import (
    DEFAULT_TIMEOUT_SECONDS,
    create_embeddings_for_question,
)


@admin.action(description="(Re)Embed selected Consultations")
def update_embeddings_admin(modeladmin, request, queryset):
    queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)
    for consultation in queryset:
        for question in consultation.question_set.all():
            queue.enqueue(create_embeddings_for_question, question.id)

    modeladmin.message_user(request, f"Processing {queryset.count()} consultations")


def _reimport_demographics(consultation_id):
    respondents = Respondent.objects.filter(consultation_id=consultation_id).extra(
        select={"old_demographics": "old_demographics"}
    )

    for respondent in respondents:
        demographics = []
        if hasattr(respondent, "old_demographics") and respondent.old_demographics:
            old_demographics = json.loads(respondent.old_demographics)
            if not isinstance(old_demographics, dict):
                raise ValueError(f"expected dict but got {type(old_demographics)}")

            for name, value in old_demographics.items():
                if name and value:
                    do, _ = DemographicOption.objects.get_or_create(
                        consultation=respondent.consultation,
                        field_name=name,
                        field_value=value,
                    )
                    demographics.append(do)
            respondent.demographics.set(demographics)


@admin.action(description="re import demographic options")
def reimport_demographics(modeladmin, request, queryset):
    queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)
    for consultation in queryset:
        queue.enqueue(_reimport_demographics, consultation.id)


class ResponseAdmin(admin.ModelAdmin):
    list_filter = ["question", "question__consultation"]
    list_display = ["free_text", "question"]
    list_select_related = True
    readonly_fields = [
        "respondent",
        "question",
        "free_text",
        "search_vector",
    ]


def create_dummy_consultation(modeladmin, request, queryset, size=10):
    if len(queryset) != 1:
        modeladmin.message_user(
            request,
            "Do not run this action on more than one consultation at a time",
            level=messages.ERROR,
        )
        return

    consultation = queryset.first()
    if consultation.question_set.count() > 0:
        modeladmin.message_user(
            request, "You should only run this on an empty consultation", level=messages.ERROR
        )
        return

    create_dummy_consultation_from_yaml_job.delay(
        number_respondents=size, consultation=consultation
    )


@admin.action(description="create small dummy consultation")
def create_small_dummy_consultation(modeladmin, request, queryset):
    create_dummy_consultation(modeladmin, request, queryset, 10)


@admin.action(description="create large dummy consultation")
def create_large_dummy_consultation(modeladmin, request, queryset):
    create_dummy_consultation(modeladmin, request, queryset, 10_000)


@admin.action(description="find themes")
def theme_identifier_action(modeladmin, request, queryset):
    query = get_queue(default_timeout=100_000)
    for consultation in queryset:
        for question in Question.objects.filter(consultation=consultation):
            query.enqueue(theme_identifier, question)


@admin.action(description="map themes")
def theme_mapper_action(modeladmin, request, queryset):
    query = get_queue(default_timeout=100_000)
    for consultation in queryset:
        for question in Question.objects.filter(consultation=consultation):
            sync_detail_detection_job = query.enqueue(sync_detail_detection, question)
            query.enqueue(sync_theme_mapping, question, depends_on=sync_detail_detection_job)


class ConsultationAdmin(admin.ModelAdmin):
    actions = [
        update_embeddings_admin,
        reimport_demographics,
        create_small_dummy_consultation,
        create_large_dummy_consultation,
        theme_identifier_action,
        theme_mapper_action,
    ]


class MultiChoiceAnswerInline(admin.StackedInline):
    model = MultiChoiceAnswer
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]
    list_display = ["consultation"]
    list_select_related = True
    readonly_fields = [
        "consultation",
        "text",
        "number",
        "has_free_text",
        "has_multiple_choice",
    ]
    inlines = [MultiChoiceAnswerInline]


class ResponseAnnotationAdmin(SimpleHistoryAdmin):
    readonly_fields = [
        "response",
        "themes",
        "sentiment",
        "evidence_rich",
        "human_reviewed",
        "reviewed_by",
        "reviewed_at",
    ]


class ResponseAnnotationThemeAdmin(admin.ModelAdmin):
    readonly_fields = [
        "response_annotation",
        "theme",
        "assigned_by",
    ]


class RespondentAdmin(admin.ModelAdmin):
    readonly_fields = ["consultation", "themefinder_id"]


class DemographicOptionAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]
    readonly_fields = ["consultation", "field_name", "field_value"]


class SelectedThemeInline(admin.StackedInline):
    model = SelectedTheme
    extra = 0


class CandidateThemeInline(admin.StackedInline):
    model = CandidateTheme
    extra = 0


class CrossCuttingThemeAdmin(admin.ModelAdmin):
    inlines = [SelectedThemeInline, CandidateThemeInline]


class CandidateThemeAdmin(admin.ModelAdmin):
    pass


admin.site.register(CandidateTheme, CandidateThemeAdmin)
admin.site.register(CrossCuttingTheme, CrossCuttingThemeAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ResponseAnnotation, ResponseAnnotationAdmin)
admin.site.register(ResponseAnnotationTheme, ResponseAnnotationThemeAdmin)
admin.site.register(Respondent, RespondentAdmin)
admin.site.register(DemographicOption, DemographicOptionAdmin)
