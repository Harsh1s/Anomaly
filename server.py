import json
import uvicorn
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException

from database import DatabaseManager
from detection import AnomalyDetector


class Server:
    def __init__(self, port: int = 8000) -> None:
        self.port = port
        self.db = DatabaseManager()
        self.detector = AnomalyDetector()
        self.clients = {}

        self.app = FastAPI()
        self.templates = Jinja2Templates(directory="templates")

        # Add routes
        self.app.websocket("/ws")(self.ws_handler)
        self.app.get("/")(self.list_clients)
        self.app.get("/clients/{client_id}")(self.client_details)

    async def ws_handler(self, websocket: WebSocket):
        """
        Handles WebSocket connections.
        The first message from the client is expected to be metadata containing the client ID and window size for anomaly detection.
        The subsequent messages are data points to be processed, each containing a timestamp and value.
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
            self.db.add_client(client_id)

            # Listen for data points
            while True:
                message = await websocket.receive_text()
                data_point = json.loads(message)
                timestamp = data_point.get("timestamp")
                value = data_point.get("value")

                if timestamp is None or value is None:
                    await websocket.send_text(
                        json.dumps({"error": "Invalid data point"})
                    )
                    continue

                # Add data point to the database and perform anomaly detection
                window_points = self.db.get_window_points(client_id, int(window))

                # If the window size is not reached, just add the point to the database
                # and respond to the client with the anomaly status as False
                if len(window_points) < window:
                    self.db.add_point(client_id, timestamp, value, 0)
                    await websocket.send_text(
                        json.dumps({"timestamp": timestamp, "anomaly": 0})
                    )
                    continue

                values = [point[1] for point in window_points] + [value]

                anomaly = self.detector.detect_anomaly(values)
                self.db.add_point(client_id, timestamp, value, anomaly)

                # Respond to the client with anomaly status
                await websocket.send_text(
                    json.dumps({"timestamp": timestamp, "anomaly": anomaly})
                )

        except WebSocketDisconnect:
            if client_id in self.clients:
                del self.clients[client_id]
                self.db.update_client_last_seen(client_id)

        except Exception as e:
            print(f"Error in WebSocket connection: {e}")

    async def list_clients(self, request: Request):
        """
        Returns a list of all clients.
        """
        clients = self.db.get_all_clients()
        return self.templates.TemplateResponse(
            "list_clients.html",
            {"request": request, "clients": clients},
        )

    async def client_details(self, request: Request, client_id: str):
        """
        Returns detailed information about a specific client.
        """
        points = self.db.get_all_client_points(client_id)
        if not points:
            raise HTTPException(status_code=404, detail="Client not found")

        is_live = client_id in self.clients
        return self.templates.TemplateResponse(
            "client_details.html",
            {
                "request": request,
                "client_id": client_id,
                "is_live": is_live,
                "points": json.dumps(
                    [
                        {"timestamp": point[0], "value": point[1], "anomaly": point[2]}
                        for point in points
                    ]
                ),
            },
        )

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
    server = Server(port=3000)
    server.run()
