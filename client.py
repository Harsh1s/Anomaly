import os
import json
import uuid
import asyncio
import random
import pandas as pd
from websockets import connect


class Client:
    def __init__(
        self,
        endpoint: str,
        port: int,
        data_file: str,
        log_dir: str,
        log_buffer_size: int = 100,
    ):
        """
        Initializes the client with the WebSocket endpoint, port, and data file.
        """
        self.endpoint = f"{endpoint}:{port}/ws"

        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file not found: {data_file}")
        self.data_file = data_file

        self.client_id = str(uuid.uuid4())  # Generate a unique client ID
        self.window = random.randint(40, 70)  # Random window size for demo

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.log_file = os.path.join(log_dir, f"{self.client_id}.log")
        self.log_buffer_size = log_buffer_size
        self.log_buffer = []

    def flush_log_buffer(self):
        """
        Flushes the log buffer to the log file.
        """
        if self.log_buffer:
            with open(self.log_file, "a") as f:
                f.write("\n".join(self.log_buffer) + "\n")
            self.log_buffer = []

    def log_message(self, message):
        """
        Logs a message to a file.
        The log buffer is flushed to the file when it reaches the buffer size.
        """
        self.log_buffer.append(message)

        if len(self.log_buffer) >= self.log_buffer_size:
            self.flush_log_buffer()

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
                self.log_message(f"Sent: {message}")

                # Wait for the server's response
                response = await websocket.recv()
                self.log_message(f"Received: {response}")

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

                self.log_message("Connection closed")
                self.flush_log_buffer()

        except Exception as e:
            print(f"Error in WebSocket connection: {e}")

    def run(self):
        """
        Runs the client asynchronously.
        """
        asyncio.run(self.connect_to_server())


if __name__ == "__main__":
    endpoint = "ws://localhost"
    port = 3000
    data_dir = "./data/"
    log_dir = "./logs/"

    async def run():
        tasks = []
        for data_file in os.listdir(data_dir):
            client = Client(
                endpoint,
                port,
                os.path.join(data_dir, data_file),
                log_dir,
            )
            tasks.append(asyncio.create_task(client.connect_to_server()))
        await asyncio.gather(*tasks)

    asyncio.run(run())
