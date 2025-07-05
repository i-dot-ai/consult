from django.contrib import admin
from django_rq import get_queue

from consultation_analyser.consultations.models import Consultation, Question, Response
from consultation_analyser.support_console.ingest import DEFAULT_TIMEOUT_SECONDS, update_embeddings


@admin.action(description="(re)embed responses")
def update_embeddings_admin(modeladmin, request, queryset):
    queue = get_queue(default_timeout=DEFAULT_TIMEOUT_SECONDS)
    for consultation in queryset:
        queue.enqueue(update_embeddings, consultation.id)

    modeladmin.message_user(request, f"Processing {queryset.count()} consultations")


@admin.action(description="Delete selected (without checking)")
def delete_selected_no_confirm(modeladmin, request, queryset):
    queryset.delete()
    modeladmin.message_user(request, f"Successfully deleted {queryset.count()} items.")


class ResponseAdmin(admin.ModelAdmin):
    # list_filter = ["question"]
    # list_display = ["free_text", "question"]
    # list_select_related = True
    # actions = [update_embeddings, delete_selected_no_confirm]
    list_display = [
        "id",
    ]  # only show essential fields
    list_per_page = 5
    show_full_result_count = False


class ConsultationAdmin(admin.ModelAdmin):
    actions = [delete_selected_no_confirm, update_embeddings_admin]


class QuestionAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]
    list_display = ["slug", "consultation"]
    list_select_related = True
    actions = [delete_selected_no_confirm]


admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
