from ninja import NinjaAPI, Schema
from ninja_jwt.authentication import JWTAuth

from consultation_analyser.consultations.public_schema import ConsultationWithResponsesAndThemes, MultipleChoiceItem


api = NinjaAPI()


@api.post("/upload_data/", auth=JWTAuth())
@api.post("/upload-themed-data/")
def upload_themed_data(request, data: ConsultationWithResponsesAndThemes):
    print("printing your data")
    print(data)
    # TODO - what to do when validation errors?
    # TODO - write to DB
    return "thanks for your data!"


@api.get("/hello/", auth=JWTAuth())
def hello(request):
    print(request.user)
    return "Hello world"


