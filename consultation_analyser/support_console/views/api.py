from ninja import NinjaAPI, Schema

api = NinjaAPI()


# TODO - this is made up for testing
# We would actually like to use the already
# defined JSON Schema
class Item(Schema):
    name: str
    quantity: int


@api.post("/upload_data/")
def upload_themed_data(request, data: Item):
    print("printing your data")
    print(data)
    return "thanks for your data!"


@api.get("/hello/")
def hello(request):
    return "Hello world"
