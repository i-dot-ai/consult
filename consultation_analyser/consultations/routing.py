from django.urls import path
from consultation_analyser.consultations import consumers

"""
This list defines the routing configuration for WebSocket connections in the consultations app.

The `websocket_urlpatterns` list contains the URL patterns for WebSocket connections. It includes the following paths:
- '/ws/upload_progress/': This path is used for WebSocket connections to track the progress of file uploads.
- '/ws/worker_status/': This path is used for WebSocket connections to receive updates on worker status.

The consumers for these WebSocket connections are defined in the `consumers` module.

Note: This module requires Django to be installed.
"""
websocket_urlpatterns = [
    path('ws/upload_progress/', consumers.UploadProgressConsumer.as_asgi()),
    path('ws/worker_status/', consumers.WorkerStatus.as_asgi()),
]

