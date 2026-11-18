from typing import ClassVar

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from simple_history.admin import SimpleHistoryAdmin

from consultations.dummy_data import create_dummy_consultation_job
from consultations.models import (
    CandidateTheme,
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from consultations.services.clone import clone_consultation_job
from consultations.services.migrate_v1_to_v2 import (
    audit_consultation,
    migrate_v1_consultation_job,
)
from data_pipeline.jobs import (
    import_candidate_themes,
)

logger = settings.LOGGER


class ResponseAdmin(admin.ModelAdmin):
    list_filter: ClassVar[list] = ["question", "question__consultation"]
    list_display: ClassVar[list] = ["free_text", "question"]
    list_select_related = True
    readonly_fields: ClassVar[list] = [
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

    create_dummy_consultation_job.delay(number_respondents=size, consultation=consultation)


@admin.action(description="create small dummy consultation")
def create_small_dummy_consultation(modeladmin, request, queryset):
    create_dummy_consultation(modeladmin, request, queryset, 10)


@admin.action(description="create large dummy consultation")
def create_large_dummy_consultation(modeladmin, request, queryset):
    create_dummy_consultation(modeladmin, request, queryset, 10_000)


@admin.action(description="import candidate themes from s3")
def import_candidate_themes_from_s3_job(modeladmin, request, queryset):
    for consultation in queryset:
        logger.info(
            "starting import job with {run_date} {code}",
            run_date=consultation.timestamp,
            code=consultation.code,
        )
        try:
            import_candidate_themes.enqueue(consultation.code, consultation.timestamp)
        except Exception:
            logger.exception(
                "failed to start import_candidate_themes for {code}", code=consultation.code
            )
            messages.error(
                request,
                f"Failed to start import for '{consultation.code}' (see logs for details)",
            )


@admin.action(description="Clone consultation")
def create_cloned_consultation(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Please select exactly one consultation to clone")
        return

    consultation = queryset.first()
    try:
        clone_consultation_job.delay(consultation.id)
        messages.success(
            request,
            f"Cloning '{consultation.title}' in the background. Monitor progress in /django-rq.",
        )
    except Exception as e:
        logger.exception(
            "Error starting clone job for consultation {consultation_id}",
            consultation_id=consultation.id,
        )
        messages.error(request, f"Failed to start clone job: {e}")


@admin.action(description="Migrate consultation from V1 to V2 schema")
def migrate_v1_consultation(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Please select exactly one consultation to migrate")
        return

    consultation = queryset.first()
    return HttpResponseRedirect(
        reverse(
            "admin:consultations_consultation_migrate_v1_confirm",
            args=[consultation.id],
        )
    )


_MIGRATION_AUDIT_LABELS = {
    "responses_missing_text": "Responses whose free text will be copied into the v2 text field",
    "questions_without_type": "Questions without a v2 question type",
    "questions_open_only": "Questions that will become open questions",
    "questions_closed_only": "Questions that will become closed questions",
    "questions_hybrid": "Hybrid questions that will be split into an open question and a closed sibling",
    "questions_without_flags": "Questions with neither flag (left untyped for manual review)",
    "multiple_choice_links": "Selected options that will become individual response rows",
    "multi_choice_answers": "Multiple-choice option records (kept for v1 consumers)",
    "demographic_options": "Demographic records that will become demographic questions and responses",
    "respondent_demographic_links": "Respondent demographic links (kept for v1 consumers)",
    "missing_data_source": "This consultation is missing a survey provider",
}


class ConsultationAdmin(admin.ModelAdmin):
    actions: ClassVar[list] = [
        create_small_dummy_consultation,
        create_large_dummy_consultation,
        import_candidate_themes_from_s3_job,
        create_cloned_consultation,
        migrate_v1_consultation,
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:consultation_id>/migrate-v1-confirm/",
                self.admin_site.admin_view(self.migrate_v1_confirm_view),
                name="consultations_consultation_migrate_v1_confirm",
            ),
        ]
        return custom_urls + urls

    def migrate_v1_confirm_view(self, request, consultation_id):
        """Intermediate confirmation page for the migration admin action.

        Shows the dry-run audit (what would change and in which direction the
        classification would go) before the background job is actually
        queued, so the django admin flow needs no CLI flags.
        """
        consultation = get_object_or_404(Consultation, pk=consultation_id)

        if request.method == "POST":
            try:
                migrate_v1_consultation_job.delay(consultation.id)
                messages.success(
                    request,
                    f"Migrating '{consultation.title}' to the V2 schema in the background. "
                    "Monitor progress in /django-rq.",
                )
            except Exception as e:
                logger.exception(
                    "Error starting V1 to V2 migration job for consultation {consultation_id}",
                    consultation_id=consultation.id,
                )
                messages.error(request, f"Failed to start migration job: {e}")
            return HttpResponseRedirect(
                reverse("admin:consultations_consultation_changelist")
            )

        already_migrated = consultation.migrated_at is not None
        has_provider = consultation.data_source is not None
        counts = (
            [
                (_MIGRATION_AUDIT_LABELS[key], value)
                for key, value in audit_consultation(consultation).items()
            ]
            if not already_migrated and not has_provider
            else []
        )
        context = {
            **self.admin_site.each_context(request),
            "title": f"Confirm v1 to v2 migration: {consultation.title}",
            "consultation": consultation,
            "counts": counts,
            "already_migrated": already_migrated,
            "has_provider": has_provider,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request, "admin/consultations/consultation/migrate_v1_confirm.html", context
        )


class MultiChoiceAnswerInline(admin.StackedInline):
    model = MultiChoiceAnswer
    extra = 0


class SelectedThemeInline(admin.StackedInline):
    model = SelectedTheme
    extra = 0


@admin.action(description="set has_free_text to false")
def set_has_free_text_false(modeladmin, request, queryset):
    queryset.update(has_free_text=False)


@admin.action(description="reset sign_off")
def reset_sign_off(modeladmin, request, queryset):
    queryset.update(theme_status=Question.ThemeStatus.DRAFT)


class QuestionAdmin(admin.ModelAdmin):
    list_filter: ClassVar[list] = ["consultation"]
    list_display: ClassVar[list] = ["text", "number", "consultation"]
    list_select_related = True
    readonly_fields: ClassVar[list] = [
        "consultation",
        "text",
        "number",
        "has_free_text",
        "has_multiple_choice",
    ]
    inlines: ClassVar[list] = [MultiChoiceAnswerInline]
    actions: ClassVar[list] = [set_has_free_text_false, reset_sign_off]
    change_form_template = "admin/consultations/question/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<uuid:question_id>/sample-responses/",
                self.admin_site.admin_view(self.sample_responses_view),
                name="consultations_question_sample_responses",
            ),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        question = self.get_object(request, object_id)
        if question:
            extra_context["non_empty_response_count"] = question.get_non_empty_responses().count()
        return super().change_view(request, object_id, form_url, extra_context)

    def sample_responses_view(self, request, question_id):
        question = Question.objects.get(pk=question_id)

        if request.method == "POST":
            try:
                keep_count = int(request.POST.get("num_responses", 0))
            except ValueError:
                messages.error(request, "Invalid number of responses")
                return HttpResponseRedirect(
                    reverse("admin:consultations_question_change", args=[question_id])
                )

            try:
                result = question.sample_responses(keep_count)
                messages.success(
                    request,
                    f"Sampled responses for question {question.number}. "
                    f"Kept {result.kept}, deleted {result.deleted} responses.",
                )
            except ValueError as e:
                messages.error(request, str(e))

        return HttpResponseRedirect(
            reverse("admin:consultations_question_change", args=[question_id])
        )


class ResponseAnnotationAdmin(SimpleHistoryAdmin):
    readonly_fields: ClassVar[list] = [
        "response",
        "themes",
        "sentiment",
        "evidence_rich",
        "human_reviewed",
        "reviewed_by",
        "reviewed_at",
    ]


class ResponseAnnotationThemeAdmin(admin.ModelAdmin):
    readonly_fields: ClassVar[list] = [
        "response_annotation",
        "theme",
        "assigned_by",
    ]


class RespondentAdmin(admin.ModelAdmin):
    readonly_fields: ClassVar[list] = ["consultation", "themefinder_id"]


class DemographicOptionAdmin(admin.ModelAdmin):
    list_filter: ClassVar[list] = ["consultation"]
    readonly_fields: ClassVar[list] = ["consultation", "field_name", "field_value"]


class CandidateThemeAdmin(admin.ModelAdmin):
    list_filter: ClassVar[list] = ["question__consultation", "question"]
    list_display: ClassVar[list] = ["name", "question", "approximate_frequency"]


class SelectedThemeAdmin(admin.ModelAdmin):
    list_filter: ClassVar[list] = ["question__consultation", "question"]
    list_display: ClassVar[list] = ["name", "question", "key"]


admin.site.register(CandidateTheme, CandidateThemeAdmin)
admin.site.register(SelectedTheme, SelectedThemeAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ResponseAnnotation, ResponseAnnotationAdmin)
admin.site.register(ResponseAnnotationTheme, ResponseAnnotationThemeAdmin)
admin.site.register(Respondent, RespondentAdmin)
admin.site.register(DemographicOption, DemographicOptionAdmin)
