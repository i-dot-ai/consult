from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations.upload_consultation import upload_consultation

from .. import models
from ..forms.consultation_upload_form import ConsultationUploadForm
from .decorators import user_can_see_consultation


@login_required
def index(request: HttpRequest) -> HttpResponse:
    consultations = request.user.consultation_set.all()
    user = request.user
    is_staff = user.is_staff
    context = {"consultations": consultations, "is_staff": is_staff}
    return render(request, "all-consultations.html", context)


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)

    context = {"questions": questions, "consultation": consultation}

    return render(request, "consultation.html", context)


@login_required
def processing(request: HttpRequest) -> HttpResponse:
    return render(request, "consultation-processing.html", {})


@login_required
def new(request: HttpRequest):
    if not request.POST:
        form = ConsultationUploadForm()
    else:
        form = ConsultationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_consultation(request.FILES["consultation_json"], request.user)
            return render(request, "consultation-uploaded.html", {})

    return render(request, "new-consultation.html", {"form": form})
