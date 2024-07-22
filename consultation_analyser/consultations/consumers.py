import json
from channels.generic.websocket import AsyncWebsocketConsumer

class UploadProgressConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling upload progress updates.
    """

    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        Adds the consumer to the "upload_progress" group and accepts the connection.
        """
        await self.channel_layer.group_add("upload_progress", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        Removes the consumer from the "upload_progress" group.
        """
        await self.channel_layer.group_discard("upload_progress", self.channel_name)

    async def receive(self, text_data):
        """
        Called when the WebSocket receives a message from the client.
        Parses the received data and handles it accordingly.
        """
        data = json.loads(text_data)

    async def upload_progress(self, event):
        """
        Called when an upload progress event is received.
        Sends the progress percentage to all connected clients.
        """
        percentage = event['percentage']
        await self.send(text_data=json.dumps({
            'percentage': percentage
        }))



class WorkerStatus(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling worker status updates.
    """

    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        Adds the consumer to the "worker_status" group and accepts the connection.
        """
        await self.channel_layer.group_add("worker_status", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket closes for any reason.
        Removes the consumer from the "worker_status" group.
        """
        await self.channel_layer.group_discard("worker_status", self.channel_name)

    async def receive(self, text_data):
        """
        Called when a WebSocket frame is received.
        Parses the received JSON data.
        """
        data = json.loads(text_data)

    async def worker_status(self, event):
        """
        Called when a worker status event is received.
        Sends the worker job ID back to the client.
        """
        worker_job_id = event['worker_job_id']
        await self.send(text_data=json.dumps({
            'worker_job_id': worker_job_id
        }))