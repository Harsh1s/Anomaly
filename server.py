import json
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from database import DatabaseManager
from detection import AnomalyDetector


class Server:
    def __init__(self, port: int = 8000) -> None:
        self.port = port
        self.db = DatabaseManager()
        self.detector = AnomalyDetector()
        self.clients = {}

        self.app = FastAPI()
        self.app.websocket("/ws")(self.ws_handler)

    async def ws_handler(self, websocket: WebSocket):
        """
        Handles WebSocket connections.
        The first message from the client should be a JSON containing client_id and window size.
        """
        await websocket.accept()

        try:
            metadata = await websocket.receive_text()
            metadata = json.loads(metadata)
            client_id = metadata.get("client_id")
            window = metadata.get("window")

            if not client_id or not window:
                await websocket.close(code=4001)
                return

            # Register the client
            self.clients[client_id] = {
                "websocket": websocket,
                "window": int(window),
            }

            # Listen for data points
            while True:
                message = await websocket.receive_text()
                data_point = json.loads(message)
                timestamp = data_point.get("timestamp")
                value = data_point.get("value")

                if timestamp is None or value is None:
                    await websocket.sent_text(
                        json.dumps({"error": "Invalid data point"})
                    )
                    continue

                # Add data point to the database and perform anomaly detection
                window_points = self.db.get_window_points(client_id, int(window))
                values = [point[1] for point in window_points] + [value]

                anomaly = self.detector.detect_anomaly(values)
                self.db.add_point(client_id, timestamp, value, anomaly)

                # Respond to the client with anomaly status
                await websocket.send_text(
                    json.dumps({"timestamp": timestamp, "anomaly": anomaly})
                )

        # Handle client disconnection
        except WebSocketDisconnect:
            if client_id in self.clients:
                del self.clients[client_id]

        except Exception as e:
            print(f"Error: {e}")
            await websocket.close()

    def run(self):
        """
        Runs the server on the specified port.
        """

        print(f"Starting server on port {self.port}...")
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
        )


if __name__ == "__main__":
    server = Server(port=8000)
    server.main()
