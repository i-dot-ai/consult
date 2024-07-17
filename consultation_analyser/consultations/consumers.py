import json
from channels.generic.websocket import WebsocketConsumer

class UploadProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def send_progress(self, event):
        progress = event['progress']
        self.send(text_data=json.dumps({
            'progress': progress
        }))
