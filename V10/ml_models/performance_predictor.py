from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor


@dataclass
class PerformancePrediction:
    predicted_score_10: float
    confidence_0_1: float
    skill_gaps: List[str]


class PerformancePredictor:
    """
    Lightweight hackathon-safe predictor.
    Trains a simple regressor from prior attempts (if available) and predicts expected score.
    """

    def __init__(self, *, model_path: Path):
        self._model_path = model_path
        self._model: Optional[RandomForestRegressor] = None

    def _features_from_attempt(self, attempt: Dict[str, Any]) -> List[float]:
        # attempt: role/field/difficulty/avg_score/time_taken + optional rubric aggregates
        diff = (attempt.get("difficulty") or "").lower()
        diff_val = 0.5
        if diff == "easy":
            diff_val = 0.2
        elif diff == "hard":
            diff_val = 0.8

        time_taken = float(attempt.get("time_taken") or 0.0)
        return [
            diff_val,
            np.log1p(max(0.0, time_taken)),
        ]

    def fit(self, *, attempts: List[Dict[str, Any]]) -> bool:
        rows: List[List[float]] = []
        y: List[float] = []
        for a in attempts or []:
            score = a.get("average_score_10")
            try:
                score_f = float(score)
            except Exception:
                continue
            rows.append(self._features_from_attempt(a))
            y.append(score_f)

        if len(rows) < 10:
            return False

        X = np.asarray(rows, dtype="float32")
        yv = np.asarray(y, dtype="float32")
        model = RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            min_samples_leaf=2,
        )
        model.fit(X, yv)
        self._model = model
        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model}, self._model_path)
        return True

    def load_if_present(self) -> bool:
        if not self._model_path.exists():
            return False
        blob = joblib.load(self._model_path)
        self._model = blob.get("model")
        return self._model is not None

    def predict(
        self,
        *,
        latest_attempt: Dict[str, Any],
        skill_gaps: List[str],
    ) -> PerformancePrediction:
        # If not trained, fall back to a stable heuristic.
        base = float(latest_attempt.get("average_score_10") or 0.0)

        if self._model is None:
            # nudge expected score based on gaps size
            gap_penalty = min(2.0, 0.15 * float(len(skill_gaps or [])))
            pred = max(0.0, min(10.0, base - gap_penalty))
            conf = 0.35
            return PerformancePrediction(predicted_score_10=round(pred, 2), confidence_0_1=conf, skill_gaps=skill_gaps[:10])

        x = np.asarray([self._features_from_attempt(latest_attempt)], dtype="float32")
        pred = float(self._model.predict(x)[0])
        pred = max(0.0, min(10.0, pred))
        return PerformancePrediction(predicted_score_10=round(pred, 2), confidence_0_1=0.7, skill_gaps=skill_gaps[:10])

