import numpy as np
from scipy.stats import iqr
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    def __init__(self):
        """
        Initializes the anomaly detector by setting the thresholds for anomaly detection.
        """
        self.thresholds = {
            "majority_voting": 0.5,  # Lowered to detect more anomalies
            "z_score": 2,            # Lowered threshold
            "iqr": 1.5,
            "ewma": {
                "alpha": 0.3,
                "threshold": 5,  # Lower threshold for EWMA detection
            },
            "moving_average": {
                "window": 5,      # Shorter moving average window
                "threshold": 3,   # Lower threshold for moving average
            },
            "modified_z_score": {
                "threshold": 3.5  # Modified Z-score threshold
            },
            "isolation_forest": {
                "n_estimators": 100,
                "contamination": 0.1,
            },
        }

        # List of anomaly detection methods
        self.detectors = [
            self.z_score_detector,
            self.iqr_detector,
            self.ewma_detector,
            self.moving_average_detector,
            self.modified_z_score_detector,
            self.isolation_forest_detector,
        ]

    def detect_anomaly(self, data):
        """
        Detects anomalies in the given data for the last data point.
        Ensembles multiple anomaly detection algorithms to improve accuracy.
        """
        anomaly_votes = [detector(data) for detector in self.detectors]
        anomaly_score = sum(anomaly_votes) / len(anomaly_votes)
        return int(anomaly_score >= self.thresholds["majority_voting"])

    def z_score_detector(self, data):
        """
        Detects anomalies using Z-score.
        """
        z_score = (data[-1] - np.mean(data)) / np.std(data)
        return abs(z_score) > self.thresholds["z_score"]

    def iqr_detector(self, data):
        """
        Detects anomalies using Interquartile Range (IQR).
        """
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr_value = q3 - q1
        lower_bound = q1 - self.thresholds["iqr"] * iqr_value
        upper_bound = q3 + self.thresholds["iqr"] * iqr_value
        return data[-1] < lower_bound or data[-1] > upper_bound

    def ewma_detector(self, data):
        """
        Detects anomalies using Exponentially Weighted Moving Average (EWMA).
        """
        ewma = [data[0]]
        alpha = self.thresholds["ewma"]["alpha"]

        for i in range(1, len(data)):
            ewma.append(alpha * data[i] + (1 - alpha) * ewma[-1])
        residual = data[-1] - ewma[-1]
        return abs(residual) > self.thresholds["ewma"]["threshold"]

    def moving_average_detector(self, data):
        """
        Detects anomalies using Moving Average.
        """
        window_size = self.thresholds["moving_average"]["window"]
        if len(data) < window_size:
            return False
        moving_avg = np.mean(data[-window_size:])
        return abs(data[-1] - moving_avg) > self.thresholds["moving_average"]["threshold"]

    def modified_z_score_detector(self, data):
        """
        Detects anomalies using Modified Z-score.
        """
        median = np.median(data)
        mad = np.median([abs(x - median) for x in data])
        if mad == 0:
            return False
        modified_z_score = 0.6745 * (data[-1] - median) / mad
        return abs(modified_z_score) > self.thresholds["modified_z_score"]["threshold"]

    def isolation_forest_detector(self, data):
        """
        Detects anomalies using Isolation Forest.
        """
        if len(data) < 2:
            return False
        clf = IsolationForest(n_estimators=self.thresholds["isolation_forest"]["n_estimators"],
                              contamination=self.thresholds["isolation_forest"]["contamination"])
        data_reshaped = np.array(data).reshape(-1, 1)
        anomaly = clf.fit_predict(data_reshaped[-10:])  # Use last 10 points
        return anomaly[-1] == -1
