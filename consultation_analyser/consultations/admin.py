from django.contrib import admin

from consultation_analyser.consultations.models import Consultation, Question, Response
from consultation_analyser.embeddings import embed_text


@admin.action(description="(re)embed free text")
def update_embeddings(modeladmin, request, queryset):
    total = queryset.count()
    batch_size = 1_000

    for i in range(0, total, batch_size):
        responses = queryset.order_by("id")[i : i + batch_size]

        free_texts = [response.free_text for response in responses]
        embeddings = embed_text(free_texts)

        for response, embedding in zip(responses, embeddings):
            response.embedding = embedding

        Response.objects.bulk_update(responses, ["embedding"])

    modeladmin.message_user(request, f"Processed {total} responses in batches of {batch_size}")


@admin.action(description="delete")
def delete_selected_no_confirm(modeladmin, request, queryset):
    queryset.delete()
    modeladmin.message_user(request, f"Successfully deleted {queryset.count()} items.")


class ResponseAdmin(admin.ModelAdmin):
    list_filter = ["question"]
    list_display = ["free_text", "question"]
    list_select_related = True
    actions = [update_embeddings, delete_selected_no_confirm]


class ConsultationAdmin(admin.ModelAdmin):
    actions = [delete_selected_no_confirm]


class QuestionAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]
    list_display = ["title", "consultation"]
    list_select_related = True
    actions = [delete_selected_no_confirm]


admin.site.register(Response, ResponseAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
