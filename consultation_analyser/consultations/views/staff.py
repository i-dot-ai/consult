import uuid

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .. import dummy_data, ml_pipeline, models


def create_dummy_data(request: HttpRequest) -> HttpResponse:
    # TODO - sort out messages properly
    message = ""
    if request.POST:
        print(request.POST)
        if "generate_dummy_consultation" in request.POST:
            try:
                dummy_data.DummyConsultation(include_themes=False)
                message = "New consultation generated"
            except RuntimeError as error:
                message = error.args[0]
        else:
            consultation_id = request.POST.get("consultation_id")
            themes_already_exist = models.Theme.objects.filter(
                answer__question__section__consultation__id=consultation_id
            ).exists()
            if not themes_already_exist:
                ml_pipeline.save_themes_for_consultation(consultation_id=consultation_id)
                message = "Themes created for consultation"
            else:
                message = "Themes already exist for consultation"

    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "message": message}
    return render(request, "create_dummy_data.html", context=context)
