import os
import json
import uuid
import asyncio
import random
import pandas as pd
from websockets import connect


class Client:
    def __init__(self, endpoint: str, port: int, data_file: str):
        """
        Initializes the client with the WebSocket endpoint, port, and data file.
        """
        self.endpoint = f"{endpoint}:{port}/ws"

        self.data_file = data_file
        self.client_id = str(uuid.uuid4())  # Generate a unique client ID
        self.window = random.randint(40, 70)  # Random window size for demo

    async def send_data(self, websocket):
        """
        Sends data points to the server from the data file at random intervals.
        """
        try:
            data_pts = pd.read_csv(self.data_file)

            for data_point in data_pts.to_dict(orient="records"):
                # Simulate random delay between data points
                await asyncio.sleep(random.uniform(0.2, 0.4))

                timestamp = data_point.get("timestamp")
                value = data_point.get("value")
                if timestamp is None or value is None:
                    print("Skipping invalid data point:", data_point)
                    continue

                message = {"timestamp": timestamp, "value": value}
                await websocket.send(json.dumps(message))
                print(f"Sent: {message}")

                # Wait for the server's response
                response = await websocket.recv()
                print(f"Received: {response}")

        except Exception as e:
            print(f"Error in sending data: {e}")

    async def connect_to_server(self):
        """
        Connects to the server, sends metadata, and handles the WebSocket connection.
        """
        try:
            async with connect(self.endpoint) as websocket:
                metadata = {"client_id": self.client_id, "window": self.window}
                await websocket.send(json.dumps(metadata))

                print(f"Connected to server with client_id: {self.client_id}")
                await self.send_data(websocket)

        except Exception as e:
            print(f"Error in WebSocket connection: {e}")

    def run(self):
        """
        Runs the client asynchronously.
        """
        asyncio.run(self.connect_to_server())


if __name__ == "__main__":
    endpoint = "ws://localhost"
    port = 8000
    data_dir = "./sample_data/"

    for data_file in os.listdir(data_dir):
        client = Client(endpoint, port, os.path.join(data_dir, data_file))
        client.run()
