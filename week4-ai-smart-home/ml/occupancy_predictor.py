"""Lightweight occupancy inference service."""
from dataclasses import dataclass
import joblib
import numpy as np

FEATURES = ["temperature", "motion", "light", "sound", "hour"]

@dataclass
class OccupancyPrediction:
    occupied: bool
    confidence: float

class OccupancyPredictor:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    def predict(self, sample: dict) -> OccupancyPrediction:
        x = np.array([[sample[name] for name in FEATURES]], dtype=float)
        probabilities = self.model.predict_proba(x)[0]
        index = int(np.argmax(probabilities))
        return OccupancyPrediction(occupied=bool(index), confidence=float(probabilities[index]))
