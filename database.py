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
        Create a SQLite database with tables for timeseries and clients.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS timeseries (
                    client_id TEXT,
                    timestamp INTEGER,
                    value REAL,
                    anomaly INTEGER DEFAULT 0
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    client_id TEXT PRIMARY KEY,
                    last_seen INTEGER
                )
                """
            )

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_timestamp ON timeseries(client_id, timestamp)"
            )
            conn.commit()

    def add_client(self, client_id: str):
        """
        Registers a new client or updates its last seen timestamp.
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO clients (client_id, last_seen)
                VALUES (?, strftime('%s', 'now'))
                ON CONFLICT(client_id) DO UPDATE SET last_seen = strftime('%s', 'now')
                """,
                (client_id,),
            )
            conn.commit()

    def get_all_clients(self):
        """
        Fetches all clients that have ever connected.
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT client_id, last_seen FROM clients")
            return cursor.fetchall()

    def update_client_last_seen(self, client_id: str):
        """
        Updates the last seen timestamp for a client.
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clients SET last_seen = strftime('%s', 'now') WHERE client_id = ?",
                (client_id,),
            )
            conn.commit()

    def get_window_points(self, client_id: str, window: int):
        """
        Fetches the most recent data points for a given client and window size.
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, value FROM timeseries WHERE client_id = ? ORDER BY timestamp DESC LIMIT ?",
                (client_id, window),
            )
            rows = cursor.fetchall()
            return rows[::-1]

    def get_all_client_points(self, client_id: str):
        """
        Fetches all data points for a given client.
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
        Saves a data point to the database.
        """
        with self.lock, sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO timeseries (client_id, timestamp, value, anomaly) VALUES (?, ?, ?, ?)",
                (client_id, timestamp, value, int(anomaly)),
            )
            conn.commit()
