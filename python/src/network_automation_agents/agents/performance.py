"""Performance Monitoring Agent."""

from typing import Any, Callable, Mapping

from ..config import Settings
from ..tools import AnomalyDetectionInput, AnomalyDetectionTool
from .base import AbstractNetworkAgent


class PerformanceMonitoringAgent(AbstractNetworkAgent):
    """Analyzes performance metrics and detects anomalies."""

    def __init__(self, settings: Settings, **kwargs: Any) -> None:
        super().__init__(
            settings,
            role="Performance Monitoring Agent",
            goal="Detect performance degradations and maintain service health baselines.",
            backstory=(
                "You are the vigilant guardian of latency, jitter, and throughput. You live in the "
                "metrics, spotting trouble before humans can blink."
            ),
            allow_delegation=False,
            verbose=False,
            **kwargs,
        )

    def tool_factories(self) -> Mapping[str, Callable[[], Any]]:
        return {"anomaly": AnomalyDetectionTool}

    def analyze_metrics(self, data_points, context):
        tool: AnomalyDetectionTool = self.get_tool("anomaly")
        params = AnomalyDetectionInput(data_stream=data_points, context=context)
        return tool.analyze(params)
