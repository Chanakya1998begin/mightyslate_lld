"""Performance monitoring tool implementations."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Sequence

try:  # pragma: no cover - optional dependency
    import httpx  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when httpx missing
    httpx = None  # type: ignore[assignment]

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class TimeSeriesDataPoint(BaseModel):
    """A single timestamped metric sample."""

    timestamp: int = Field(..., description="Unix timestamp in seconds.")
    value: float = Field(..., description="Numeric value for the metric.")


class TimeSeriesResult(BaseModel):
    """Result set for a single metric series."""

    metric: Dict[str, str] = Field(default_factory=dict, description="Metric labels (e.g., device, interface).")
    values: List[TimeSeriesDataPoint] = Field(default_factory=list, description="Ordered metric samples.")


class TSDBQueryOutput(BaseModel):
    """Structured response for time-series database queries."""

    results: List[TimeSeriesResult] = Field(default_factory=list, description="Collection of time series results.")


class TSDBQueryTool:
    """Wrapper for querying a time-series database (Prometheus/Influx/etc.)."""

    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None) -> None:
        self._base_url = base_url
        self._api_token = api_token
        self._logger = build_logger("TSDBQueryTool")

    def query(self, query: str) -> ToolOutput:
        if not query.strip():
            return ToolOutput.fail("Query string must not be empty")

        if httpx is None or self._base_url is None:
            self._logger.warning("tsdb_httpx_unavailable", base_url=self._base_url)
            return ToolOutput.ok(self._synthetic_response(query))

        try:
            headers = {"Authorization": f"Bearer {self._api_token}"} if self._api_token else None
            response = httpx.get(f"{self._base_url}/api/v1/query", params={"query": query}, headers=headers, timeout=10.0)
            response.raise_for_status()
            parsed = self._parse_prometheus_response(response.json())
            return ToolOutput.ok(parsed)
        except Exception as exc:  # pragma: no cover - network failures are environment-specific
            self._logger.error("tsdb_query_failed", error=str(exc))
            return ToolOutput.fail("TSDB query failed", details={"error": str(exc)})

    def _parse_prometheus_response(self, payload: Dict[str, Any]) -> TSDBQueryOutput:
        status = payload.get("status")
        if status != "success":
            raise RuntimeError(f"Unexpected TSDB status: {status}")
        data = payload.get("data", {})
        result_type = data.get("resultType", "vector")
        results: List[TimeSeriesResult] = []
        for item in data.get("result", []):
            metric = item.get("metric", {})
            series_values: List[TimeSeriesDataPoint] = []
            if result_type == "matrix":
                iterator = item.get("values", [])
            else:
                iterator = [item.get("value")]
            for sample in iterator:
                if not sample:
                    continue
                timestamp, value = sample
                series_values.append(TimeSeriesDataPoint(timestamp=int(float(timestamp)), value=float(value)))
            results.append(TimeSeriesResult(metric=metric, values=series_values))
        return TSDBQueryOutput(results=results)

    def _synthetic_response(self, query: str) -> TSDBQueryOutput:
        now = int(time.time())
        metric_labels = {"__synthetic__": "true", "query": query[:50]}
        samples = [TimeSeriesDataPoint(timestamp=now - offset * 60, value=1.0 + offset * 0.1) for offset in range(3)]
        return TSDBQueryOutput(results=[TimeSeriesResult(metric=metric_labels, values=list(reversed(samples)))])


class OpticalLaneDiagnostics(BaseModel):
    """Diagnostics for a single optical lane."""

    lane_id: int = Field(..., ge=0)
    rx_power_dbm: float = Field(..., description="Received optical power in dBm.")
    tx_power_dbm: float = Field(..., description="Transmit optical power in dBm.")


class OpticalDiagnosticsOutput(BaseModel):
    """Complete optical diagnostics response."""

    device: str = Field(...)
    interface: str = Field(...)
    temperature_celsius: float = Field(...)
    voltage_volts: float = Field(...)
    lanes: List[OpticalLaneDiagnostics] = Field(default_factory=list)


class OpticalDiagnosticsTool:
    """Retrieve optical telemetry using NETCONF/SNMP with graceful fallbacks."""

    def __init__(
        self,
        netconf_fetcher: Optional[Callable[[str, str], Dict[str, Any]]] = None,
        snmp_fetcher: Optional[Callable[[str, str], Dict[str, Any]]] = None,
    ) -> None:
        self._netconf_fetcher = netconf_fetcher
        self._snmp_fetcher = snmp_fetcher
        self._logger = build_logger("OpticalDiagnosticsTool")

    def get_optical_diagnostics(self, device: str, interface: str) -> ToolOutput:
        payload: Optional[Dict[str, Any]] = None
        if self._netconf_fetcher is not None:
            try:
                payload = self._netconf_fetcher(device, interface)
                self._logger.info("optical_via_netconf", device=device, interface=interface)
            except Exception as exc:  # pragma: no cover - network exceptions
                self._logger.warning("optical_netconf_failed", device=device, error=str(exc))

        if payload is None and self._snmp_fetcher is not None:
            try:
                payload = self._snmp_fetcher(device, interface)
                self._logger.info("optical_via_snmp", device=device, interface=interface)
            except Exception as exc:  # pragma: no cover
                self._logger.warning("optical_snmp_failed", device=device, error=str(exc))

        if payload is None:
            payload = self._synthetic_optics(interface)

        result = OpticalDiagnosticsOutput(
            device=device,
            interface=interface,
            temperature_celsius=float(payload.get("temperature_celsius", 42.0)),
            voltage_volts=float(payload.get("voltage_volts", 3.3)),
            lanes=[
                OpticalLaneDiagnostics(
                    lane_id=int(lane.get("lane_id", idx)),
                    rx_power_dbm=float(lane.get("rx_power_dbm", -4.1)),
                    tx_power_dbm=float(lane.get("tx_power_dbm", -1.9)),
                )
                for idx, lane in enumerate(payload.get("lanes", []))
            ]
            or self._default_lanes(),
        )
        return ToolOutput.ok(result)

    @staticmethod
    def _synthetic_optics(interface: str) -> Dict[str, Any]:
        return {
            "temperature_celsius": 39.5,
            "voltage_volts": 3.28,
            "lanes": [
                {"lane_id": 0, "rx_power_dbm": -3.5, "tx_power_dbm": -2.0},
                {"lane_id": 1, "rx_power_dbm": -3.6, "tx_power_dbm": -1.8},
            ],
        }

    @staticmethod
    def _default_lanes() -> List[OpticalLaneDiagnostics]:
        return [
            OpticalLaneDiagnostics(lane_id=0, rx_power_dbm=-3.7, tx_power_dbm=-2.1),
            OpticalLaneDiagnostics(lane_id=1, rx_power_dbm=-3.9, tx_power_dbm=-2.0),
        ]


class BGPPeer(BaseModel):
    """State of a single BGP session."""

    peer_address: str = Field(...)
    remote_as: int = Field(..., ge=0)
    state: str = Field(...)
    prefixes_received: int = Field(..., ge=0)
    uptime_sec: int = Field(..., ge=0)


class BGPHealthOutput(BaseModel):
    """Aggregate BGP health report."""

    device: str = Field(...)
    peers: List[BGPPeer] = Field(default_factory=list)


class RoutingHealthTool:
    """Query routing protocol health via NETCONF/SNMP."""

    def __init__(
        self,
        summary_fetcher: Optional[Callable[[str], Sequence[Dict[str, Any]]]] = None,
    ) -> None:
        self._summary_fetcher = summary_fetcher
        self._logger = build_logger("RoutingHealthTool")

    def get_bgp_summary(self, device: str) -> ToolOutput:
        peer_data: Sequence[Dict[str, Any]]
        if self._summary_fetcher is not None:
            try:
                peer_data = self._summary_fetcher(device)
                self._logger.info("bgp_summary_external", device=device, peers=len(peer_data))
            except Exception as exc:  # pragma: no cover - transport specific
                self._logger.warning("bgp_summary_failed", device=device, error=str(exc))
                peer_data = self._synthetic_bgp(device)
        else:
            peer_data = self._synthetic_bgp(device)

        peers = [
            BGPPeer(
                peer_address=item.get("peer_address", "0.0.0.0"),
                remote_as=int(item.get("remote_as", 0)),
                state=item.get("state", "Idle"),
                prefixes_received=int(item.get("prefixes_received", 0)),
                uptime_sec=int(item.get("uptime_sec", 0)),
            )
            for item in peer_data
        ]
        return ToolOutput.ok(BGPHealthOutput(device=device, peers=peers))

    def _synthetic_bgp(self, device: str) -> List[Dict[str, Any]]:
        self._logger.info("bgp_summary_synthetic", device=device)
        return [
            {
                "peer_address": "203.0.113.1",
                "remote_as": 64512,
                "state": "Established",
                "prefixes_received": 420,
                "uptime_sec": 86400,
            },
            {
                "peer_address": "198.51.100.2",
                "remote_as": 64513,
                "state": "Idle",
                "prefixes_received": 0,
                "uptime_sec": 0,
            },
        ]


class SyntheticProbeRequest(BaseModel):
    """Definition of an active synthetic probe."""

    source: str = Field(..., description="Probe source location or agent")
    destination: str = Field(..., description="Destination hostname or IP")
    test_type: str = Field(..., description="Probe type, e.g., http, ping, path_trace")
    frequency_sec: int = Field(..., gt=0, description="Probe execution cadence in seconds.")


class SyntheticProbeStatus(BaseModel):
    """Runtime status for a synthetic probe."""

    probe_id: str = Field(...)
    source: str = Field(...)
    destination: str = Field(...)
    test_type: str = Field(...)
    status: str = Field(...)
    last_checked_epoch: int = Field(...)


class SyntheticProbeManagementTool:
    """Manage synthetic probes via an abstract backend."""

    def __init__(
        self,
        backend: Optional[Callable[[str, SyntheticProbeRequest], ToolOutput]] = None,
    ) -> None:
        self._backend = backend
        self._logger = build_logger("SyntheticProbeManagementTool")
        self._in_memory_state: Dict[str, SyntheticProbeStatus] = {}

    def manage_probe(self, probe_id: str, request: SyntheticProbeRequest, action: str) -> ToolOutput:
        action = action.lower()
        if action not in {"create", "delete", "get"}:
            return ToolOutput.fail("Unsupported action", details={"action": action})

        if self._backend is not None:
            try:
                return self._backend(action, request)
            except Exception as exc:  # pragma: no cover - backend specific
                self._logger.warning("synthetic_probe_backend_failed", action=action, error=str(exc))

        if action == "create":
            status = SyntheticProbeStatus(
                probe_id=probe_id,
                source=request.source,
                destination=request.destination,
                test_type=request.test_type,
                status="scheduled",
                last_checked_epoch=int(time.time()),
            )
            self._in_memory_state[probe_id] = status
            self._logger.info("synthetic_probe_created", probe_id=probe_id)
            return ToolOutput.ok(status)

        if action == "delete":
            removed = self._in_memory_state.pop(probe_id, None)
            if removed is None:
                return ToolOutput.fail("Probe not found", details={"probe_id": probe_id})
            self._logger.info("synthetic_probe_deleted", probe_id=probe_id)
            return ToolOutput.ok({"probe_id": probe_id, "status": "deleted"})

        status = self._in_memory_state.get(probe_id)
        if status is None:
            return ToolOutput.fail("Probe not found", details={"probe_id": probe_id})
        refreshed = status.model_copy(update={"last_checked_epoch": int(time.time())})
        self._in_memory_state[probe_id] = refreshed
        self._logger.info("synthetic_probe_status", probe_id=probe_id)
        return ToolOutput.ok(refreshed)


__all__ = [
    "TSDBQueryTool",
    "TimeSeriesDataPoint",
    "TimeSeriesResult",
    "TSDBQueryOutput",
    "OpticalDiagnosticsTool",
    "OpticalLaneDiagnostics",
    "OpticalDiagnosticsOutput",
    "RoutingHealthTool",
    "BGPPeer",
    "BGPHealthOutput",
    "SyntheticProbeManagementTool",
    "SyntheticProbeRequest",
    "SyntheticProbeStatus",
]
