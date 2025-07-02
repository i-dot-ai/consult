from django.contrib import admin

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ["title"]


class QuestionAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]


class RespondentAdmin(admin.ModelAdmin):
    list_filter = ["consultation"]


class ResponseAdmin(admin.ModelAdmin):
    list_filter = ["question__consultation"]


class ResponseAnnotationAdmin(admin.ModelAdmin):
    list_filter = ["question__consultation"]


class ResponseAnnotationThemeAdmin(admin.ModelAdmin):
    list_filter = ["response__question__consultation"]


class ThemeAdmin(admin.ModelAdmin):
    list_filter = ["question__consultation"]


admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Respondent, RespondentAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(ResponseAnnotation, ResponseAnnotationAdmin)
admin.site.register(ResponseAnnotationTheme, ResponseAnnotationThemeAdmin)
admin.site.register(Theme, ThemeAdmin)
