"""Analytics and machine learning tooling wrappers."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

try:  # pragma: no cover - heavy dependency optional during tests
    import numpy as np  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    np = None  # type: ignore[assignment]

try:  # pragma: no cover
    from sklearn.ensemble import IsolationForest  # type: ignore[import-not-found]
    from sklearn.linear_model import LogisticRegression  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    IsolationForest = None  # type: ignore[assignment]
    LogisticRegression = None  # type: ignore[assignment]

from ..logging import build_logger
from ..models import ToolOutput


class AnomalyDetectionInput(BaseModel):
    data_stream: List[float] = Field(..., description="Recent metric values.")
    context: Dict[str, str] = Field(default_factory=dict, description="Additional metadata.")


class PredictiveMaintenanceInput(BaseModel):
    device: str = Field(..., description="Device identifier.")
    metric_history: List[float] = Field(..., description="Historical metric values for prediction.")
    component_id: str = Field(
        default="unknown",
        description="Identifier for the component or subsystem being evaluated.",
    )


class FailurePrediction(BaseModel):
    device: str = Field(..., description="Device identifier")
    component_id: str = Field(..., description="Component or subsystem identifier")
    failure_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of failure in the next window")
    predicted_time_to_failure_hours: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated hours before failure, when available.",
    )
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="List of notable signals that influenced the prediction.",
    )


class AnomalyDetectionTool:
    """Simple isolation forest wrapper."""

    def __init__(self) -> None:
        self._logger = build_logger("AnomalyDetectionTool")
        if IsolationForest is not None and np is not None:
            self._model = IsolationForest(contamination=0.02, random_state=42)
        else:
            self._model = None

    def analyze(self, params: AnomalyDetectionInput) -> ToolOutput:
        if len(params.data_stream) < 5:
            return ToolOutput.fail("Insufficient data for anomaly detection")
        if self._model is None or np is None:
            mean = sum(params.data_stream[:-1]) / (len(params.data_stream) - 1)
            latest = params.data_stream[-1]
            deviation = latest - mean
            threshold = 3 * (abs(mean) + 1e-5)
            is_anomaly = abs(deviation) > threshold
            latest_score = -abs(deviation)
        else:
            data = np.array(params.data_stream).reshape(-1, 1)
            self._model.fit(data)
            scores = self._model.decision_function(data)
            latest_score = float(scores[-1])
            is_anomaly = latest_score < 0
        self._logger.info(
            "anomaly_analysis",
            device=params.context.get("device"),
            latest_score=latest_score,
            is_anomaly=is_anomaly,
        )
        return ToolOutput.ok(
            {
                "anomaly": is_anomaly,
                "score": latest_score,
                "context": params.context,
            }
        )


class PredictiveMaintenanceTool:
    """Logistic regression stub for failure probability predictions."""

    def __init__(self) -> None:
        self._logger = build_logger("PredictiveMaintenanceTool")
        if LogisticRegression is not None and np is not None:
            rng = np.random.default_rng(seed=42)
            X = rng.normal(loc=0.0, scale=1.0, size=(100, 3))
            y = (X[:, 0] + X[:, 1] * 0.2 > 0.5).astype(int)
            self._model = LogisticRegression()
            self._model.fit(X, y)
        else:
            self._model = None

    def predict(self, params: PredictiveMaintenanceInput) -> ToolOutput:
        if len(params.metric_history) < 3:
            return ToolOutput.fail("Need at least three data points for prediction")
        if self._model is None or np is None:
            window = params.metric_history[-3:]
            prediction = min(1.0, max(0.0, sum(window) / (len(window) * 100.0)))
        else:
            features = np.array(params.metric_history[-3:])
            prediction = float(self._model.predict_proba([features])[0][1])

        time_to_failure = self._estimate_time_to_failure(prediction)
        contributing_factors = self._derive_contributing_factors(params.metric_history)
        result = FailurePrediction(
            device=params.device,
            component_id=params.component_id,
            failure_probability=prediction,
            predicted_time_to_failure_hours=time_to_failure,
            contributing_factors=contributing_factors,
        )
        self._logger.info(
            "predictive_maintenance",
            device=params.device,
            probability=prediction,
            component=params.component_id,
        )
        return ToolOutput.ok(result)

    @staticmethod
    def _estimate_time_to_failure(probability: float) -> Optional[int]:
        if probability >= 0.85:
            return 12
        if probability >= 0.6:
            return 48
        if probability >= 0.4:
            return 120
        return None

    @staticmethod
    def _derive_contributing_factors(metric_history: List[float]) -> List[str]:
        if len(metric_history) < 3:
            return []
        factors: List[str] = []
        recent_window = metric_history[-3:]
        if recent_window[-1] > max(metric_history[:-1]):
            factors.append("recent_peak")
        if recent_window == sorted(recent_window):
            factors.append("upward_trend")
        if max(metric_history) - min(metric_history) > 0.5 * (abs(sum(metric_history) / len(metric_history)) + 1e-5):
            factors.append("high_variability")
        return factors
