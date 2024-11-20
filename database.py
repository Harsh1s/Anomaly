import os
import sqlite3
import threading


class DatabaseManager:
    def __init__(self, db_name: str = "timeseries.db") -> None:
        self.db_name = db_name
        self.lock = threading.Lock()
        if not os.path.exists(self.db_name):
            self.create_database()

    def create_database(self):
        """
        Create a SQLite database with a single table named timeseries
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS timeseries (
                    client_id TEXT PRIMARY KEY,
                    timestamp INTEGER,
                    value REAL,
                    anomaly INTEGER DEFAULT 0
                )
                """
            )
            cursor.execute(
                "CREATE INDEX idx_client_timestamp ON timeseries(client_id, timestamp)"
            )

            conn.commit()

    def get_window_points(self, client_id: str, window: int):
        """
        Fetches all data points for a given client_id and window
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, value FROM timeseries WHERE client_id = ? ORDER BY timestamp DESC LIMIT ?",
                (client_id, window),
            )

            rows = cursor.fetchall()
            return rows.reverse()

    def get_all_client_points(self, client_id: str):
        """
        Fetches all data points for a given client_id
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, value, anomaly FROM timeseries WHERE client_id = ? ORDER BY timestamp ASC",
                (client_id,),
            )

            return cursor.fetchall()

    def add_point(self, client_id: str, timestamp: int, value: float, anomaly: bool):
        """
        Saves a data point to the database
        """

        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO timeseries (client_id, timestamp, value, anomaly) VALUES (?, ?, ?, ?)",
                (client_id, timestamp, value, int(anomaly)),
            )
            conn.commit()
