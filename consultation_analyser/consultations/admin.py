from django.contrib import admin
from django_rq import get_queue

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
)
from consultation_analyser.support_console.ingest import DEFAULT_TIMEOUT_SECONDS, update_embeddings


@admin.action(description="(Re)Embed selected Consultations")
def update_embeddings_admin(modeladmin, request, queryset):
    queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)
    for consultation in queryset:
        queue.enqueue(update_embeddings, consultation.id)

    modeladmin.message_user(request, f"Processing {queryset.count()} consultations")


class ResponseAdmin(admin.ModelAdmin):
    list_filter = ["question", "question__consultation"]
    list_display = ["free_text", "question"]
    list_select_related = True
    readonly_fields = [
        "respondent",
        "question",
        "free_text",
        "chosen_options",
        "embedding",
    ]


class ConsultationAdmin(admin.ModelAdmin):
    actions = [update_embeddings_admin]
    readonly_fields = ["title", "slug", "users"]


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
        "multiple_choice_options",
    ]


class ResponseAnnotationAdmin(admin.ModelAdmin):
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
        "is_original_ai_assignment",
        "assigned_by",
    ]


admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ResponseAnnotation, ResponseAnnotationAdmin)
admin.site.register(ResponseAnnotationTheme, ResponseAnnotationThemeAdmin)
