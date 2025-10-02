import json

from django.contrib import admin
from django_tasks import task
from simple_history.admin import SimpleHistoryAdmin

from consultation_analyser.consultations.models import (
    Consultation,
    CrossCuttingTheme,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)
from consultation_analyser.support_console.ingest import (
    create_embeddings_for_question,
)


@admin.action(description="(Re)Embed selected Consultations")
def update_embeddings_admin(modeladmin, request, queryset):
    for consultation in queryset:
        for question in consultation.question_set.all():
            create_embeddings_for_question.enqueue(str(question.id))

    modeladmin.message_user(request, f"Processing {queryset.count()} consultations")


@task(priority=10, queue_name="default")
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
    for consultation in queryset:
        _reimport_demographics.enqueue(consultation.id)


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


class ConsultationAdmin(admin.ModelAdmin):
    actions = [update_embeddings_admin, reimport_demographics]
    readonly_fields = ["title", "slug", "users"]


class MultiChoiceAnswerInline(admin.StackedInline):
    model = MultiChoiceAnswer
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]
    list_display = ["slug", "consultation"]
    list_select_related = True
    readonly_fields = [
        "consultation",
        "text",
        "slug",
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


class ThemeInline(admin.StackedInline):
    model = Theme
    extra = 0


class CrossCuttingThemeAdmin(admin.ModelAdmin):
    inlines = [ThemeInline]


admin.site.register(CrossCuttingTheme, CrossCuttingThemeAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ResponseAnnotation, ResponseAnnotationAdmin)
admin.site.register(ResponseAnnotationTheme, ResponseAnnotationThemeAdmin)
admin.site.register(Respondent, RespondentAdmin)
admin.site.register(DemographicOption, DemographicOptionAdmin)
