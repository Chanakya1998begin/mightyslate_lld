"""Security and threat detection tooling."""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

try:  # pragma: no cover - optional dependency
    import httpx  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when httpx missing
    httpx = None  # type: ignore[assignment]

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class FlowAggregate(BaseModel):
    """Aggregated flow statistics."""

    key: Dict[str, Any] = Field(..., description="Aggregation key (e.g., source/dest tuple).")
    total_bytes: int = Field(..., ge=0)
    total_packets: int = Field(..., ge=0)


class FlowAnalysisResult(BaseModel):
    """Result of a flow analysis query."""

    query: Dict[str, Any] = Field(default_factory=dict)
    time_range: str = Field(...)
    aggregates: List[FlowAggregate] = Field(default_factory=list)


class FlowAnalysisTool:
    """Analyze flow records from an external datastore."""

    def __init__(self, backend_query: Optional[Callable[[Dict[str, Any], str], Sequence[Dict[str, Any]]]] = None) -> None:
        self._backend_query = backend_query
        self._logger = build_logger("FlowAnalysisTool")

    def query_flows(self, query_filter: Dict[str, Any], time_range: str) -> ToolOutput:
        try:
            if self._backend_query is not None:
                records = self._backend_query(query_filter, time_range)
            else:
                records = self._synthetic_flows(query_filter)
        except Exception as exc:  # pragma: no cover - backend specific errors
            self._logger.error("flow_query_failed", error=str(exc))
            return ToolOutput.fail("Flow query failed", details={"error": str(exc)})

        aggregates = [
            FlowAggregate(
                key={key: record.get(key) for key in query_filter.keys()},
                total_bytes=int(record.get("bytes", 0)),
                total_packets=int(record.get("packets", 0)),
            )
            for record in records
        ]
        result = FlowAnalysisResult(query=query_filter, time_range=time_range, aggregates=aggregates)
        self._logger.info("flow_query", filter_keys=list(query_filter.keys()), time_range=time_range)
        return ToolOutput.ok(result)

    def _synthetic_flows(self, query_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        key = "-".join(f"{k}:{v}" for k, v in query_filter.items()) or "all"
        return [
            {"bytes": 125000, "packets": 1500, **{k: v for k, v in query_filter.items()}},
            {"bytes": 83000, "packets": 900, **{k: v for k, v in query_filter.items()}},
            {"bytes": 45000, "packets": 620, "anomaly": key},
        ]


class LogEvent(BaseModel):
    """Single log event."""

    source: str = Field(...)
    severity: str = Field(...)
    message: str = Field(...)
    timestamp: int = Field(..., ge=0)


class LogQueryResult(BaseModel):
    """Structured log query response."""

    query: Dict[str, Any] = Field(default_factory=dict)
    time_range: str = Field(...)
    events: List[LogEvent] = Field(default_factory=list)


class LogAnalysisTool:
    """Query security logs for relevant events."""

    def __init__(self, backend_query: Optional[Callable[[Dict[str, Any], str], Iterable[Dict[str, Any]]]] = None) -> None:
        self._backend_query = backend_query
        self._logger = build_logger("LogAnalysisTool")

    def query_logs(self, query_filter: Dict[str, Any], time_range: str) -> ToolOutput:
        try:
            if self._backend_query is not None:
                records = self._backend_query(query_filter, time_range)
            else:
                records = self._synthetic_logs(query_filter)
        except Exception as exc:  # pragma: no cover - backend errors
            self._logger.error("log_query_failed", error=str(exc))
            return ToolOutput.fail("Log query failed", details={"error": str(exc)})

        events = [
            LogEvent(
                source=str(record.get("source", "unknown")),
                severity=str(record.get("severity", "INFO")),
                message=str(record.get("message", "")),
                timestamp=int(record.get("timestamp", 0)),
            )
            for record in records
        ]
        result = LogQueryResult(query=query_filter, time_range=time_range, events=events)
        self._logger.info("log_query", count=len(events), time_range=time_range)
        return ToolOutput.ok(result)

    def _synthetic_logs(self, query_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "source": query_filter.get("source", "firewall"),
                "severity": "WARNING",
                "message": "Synthetic login failure detected",
                "timestamp": 1700000000,
            },
            {
                "source": query_filter.get("source", "ids"),
                "severity": "CRITICAL",
                "message": "Synthetic port scan detected",
                "timestamp": 1700000600,
            },
        ]


class IPReputation(BaseModel):
    """Reputation detail for an IP address."""

    ip_address: str = Field(...)
    is_malicious: bool = Field(...)
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    categories: List[str] = Field(default_factory=list)
    source: str = Field(...)


class ThreatIntelligenceTool:
    """Query external threat intelligence services."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._logger = build_logger("ThreatIntelligenceTool")

    def check_ip_reputation(self, ip_address: str) -> ToolOutput:
        if httpx is None or self._base_url is None:
            self._logger.warning("threat_intel_httpx_unavailable", ip=ip_address)
            return ToolOutput.ok(self._synthetic_reputation(ip_address))
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else None
            response = httpx.get(
                f"{self._base_url}/reputation/ip/{ip_address}",
                headers=headers,
                timeout=8.0,
            )
            response.raise_for_status()
            payload = response.json()
            reputation = IPReputation.model_validate(payload)
            return ToolOutput.ok(reputation)
        except Exception as exc:  # pragma: no cover - network specific
            self._logger.error("threat_intel_query_failed", error=str(exc))
            return ToolOutput.ok(self._synthetic_reputation(ip_address))

    def _synthetic_reputation(self, ip_address: str) -> IPReputation:
        return IPReputation(
            ip_address=ip_address,
            is_malicious=False,
            confidence_score=0.1,
            categories=["benign"],
            source="synthetic",
        )


class SecurityActionResult(BaseModel):
    """Result of a remediation action."""

    device: str = Field(...)
    action: str = Field(...)
    status: str = Field(...)
    details: Dict[str, Any] = Field(default_factory=dict)


class RemediationActionTool:
    """Apply guard-railed security remediation actions."""

    def __init__(self, block_callable: Optional[Callable[[str, str], ToolOutput]] = None) -> None:
        self._block_callable = block_callable
        self._logger = build_logger("RemediationActionTool")

    def block_ip(self, device: str, ip_to_block: str) -> ToolOutput:
        if self._block_callable is not None:
            result = self._block_callable(device, ip_to_block)
            if not isinstance(result, ToolOutput):
                return ToolOutput.fail("Invalid remediation callable response")
            if result.success:
                return ToolOutput.ok(self._result(device, ip_to_block, result.data))
            return result

        self._logger.info("remediation_block_ip", device=device, ip=ip_to_block)
        return ToolOutput.ok(self._result(device, ip_to_block, {"mode": "simulated"}))

    def _result(self, device: str, ip_to_block: str, details: Any) -> SecurityActionResult:
        if isinstance(details, dict):
            detail_dict = details
        else:
            detail_dict = {"details": details}
        detail_dict.setdefault("ip", ip_to_block)
        return SecurityActionResult(device=device, action="block_ip", status="submitted", details=detail_dict)


__all__ = [
    "FlowAnalysisTool",
    "FlowAnalysisResult",
    "FlowAggregate",
    "LogAnalysisTool",
    "LogQueryResult",
    "LogEvent",
    "ThreatIntelligenceTool",
    "IPReputation",
    "RemediationActionTool",
    "SecurityActionResult",
]
