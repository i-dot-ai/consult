from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
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
from consultation_analyser.consultations.services.clone import clone_consultation
from consultation_analyser.data_pipeline.jobs import (
    import_candidate_themes,
)

logger = settings.LOGGER


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
        except Exception as e:
            logger.error("failed to start import_candidate_themes: {error}", error=e)


@admin.action(description="Clone consultation")
def create_cloned_consultation(modeladmin, request, queryset):
    if queryset.count() != 1:
        messages.error(request, "Please select exactly one consultation to clone")
        return

    consultation = queryset.first()
    try:
        cloned = clone_consultation(consultation)
        messages.success(
            request,
            f"Successfully cloned '{consultation.title}' as '{cloned.title}'",
        )
    except Exception as e:
        logger.exception(f"Error cloning consultation {consultation.id}: {e}")
        messages.error(request, f"Failed to clone consultation: {e}")


class ConsultationAdmin(admin.ModelAdmin):
    actions = [
        create_small_dummy_consultation,
        create_large_dummy_consultation,
        import_candidate_themes_from_s3_job,
        create_cloned_consultation,
    ]


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
    list_filter = ["consultation"]
    list_display = ["text", "number", "consultation"]
    list_select_related = True
    readonly_fields = [
        "consultation",
        "text",
        "number",
        "has_free_text",
        "has_multiple_choice",
    ]
    inlines = [MultiChoiceAnswerInline]
    actions = [set_has_free_text_false, reset_sign_off]
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


class CrossCuttingThemeAdmin(admin.ModelAdmin):
    inlines = [SelectedThemeInline]


class CandidateThemeAdmin(admin.ModelAdmin):
    list_filter = ["question__consultation", "question"]
    list_display = ["name", "question", "approximate_frequency"]


class SelectedThemeAdmin(admin.ModelAdmin):
    list_filter = ["question__consultation", "question"]
    list_display = ["name", "question", "key"]


admin.site.register(CandidateTheme, CandidateThemeAdmin)
admin.site.register(SelectedTheme, SelectedThemeAdmin)
admin.site.register(CrossCuttingTheme, CrossCuttingThemeAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ResponseAnnotation, ResponseAnnotationAdmin)
admin.site.register(ResponseAnnotationTheme, ResponseAnnotationThemeAdmin)
admin.site.register(Respondent, RespondentAdmin)
admin.site.register(DemographicOption, DemographicOptionAdmin)
