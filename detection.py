import numpy as np
from scipy.stats import iqr


class AnomalyDetector:
    def __init__(self):
        """
        Initializes the anomaly detector by setting the thresholds for anomaly detection.
        """
        self.thresholds = {
            "majority_voting": 0.25,
            "z_score": 3,
            "iqr": 1.5,
            "ewma": {
                "alpha": 0.3,
                "threshold": 10,
            },
        }

        # List of anomaly detection methods
        self.detectors = [
            self.z_score_detector,
            self.iqr_detector,
            self.ewma_detector,
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
        return abs(residual) > self.thresholds["ewma"]
