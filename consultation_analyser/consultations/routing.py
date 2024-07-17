from django.urls import path
from consultation_analyser.consultations import consumers

websocket_urlpatterns = [
    path('ws/upload_progress/', consumers.UploadProgressConsumer.as_asgi()),
]