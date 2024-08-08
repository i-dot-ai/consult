import datetime
import logging

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage as storage
from ninja import NinjaAPI
from ninja_jwt.authentication import JWTAuth

from consultation_analyser.consultations.jobs.upload_consultation import async_upload_consultation
from consultation_analyser.consultations.public_schema import ConsultationWithResponses
from consultation_analyser.support_console.decorators import support_login_required

logger = logging.getLogger("api")

api = NinjaAPI()


# For now, just upload a consultation as we don't know format of themes
@api.post("/upload-consultation/", auth=JWTAuth())
@support_login_required
def upload_consultation(request, data: ConsultationWithResponses):
    logger.info("Saving uploaded consultation data")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{timestamp}-consultation-uploaded.json"
    file = ContentFile(data.json())
    file_path = storage.save(filename, file)
    async_upload_consultation.delay(file_path, request.user.id)
    return "Your data is being uploaded"


# For testing
@api.get("/hello/", auth=JWTAuth())
@support_login_required
def hello(request):
    print(request.user)
    return "Hello world"
