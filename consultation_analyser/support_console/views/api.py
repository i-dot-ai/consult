from ninja import NinjaAPI, Schema
from ninja_jwt.authentication import JWTAuth


api = NinjaAPI()



# TODO - this is made up for testing
# We would actually like to use the already
# defined JSON Schema
class Item(Schema):
    name: str
    quantity: int


@api.post("/upload_data/", auth=JWTAuth())
def upload_themed_data(request, data: Item):
    print("printing your data")
    print(data)
    return "thanks for your data!"


@api.get("/hello/", auth=JWTAuth())
def hello(request):
    return "Hello world"
