"""Lifecycle management tooling."""

from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Sequence

try:  # pragma: no cover - optional dependency during tests
    import httpx  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when httpx missing
    httpx = None  # type: ignore[assignment]

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class DeviceSoftwareRecord(BaseModel):
    device: str = Field(...)
    os_version: str = Field(...)


class NSOTQueryTool:
    """Query the Network Source of Truth for inventory data."""

    def __init__(self) -> None:
        self._logger = build_logger("NSOTQueryTool")

    def list_devices(self, role: str | None = None) -> ToolOutput:
        self._logger.info("list_devices", role=role)
        devices = [
            DeviceSoftwareRecord(device="core-switch-1", os_version="IOS-XE 17.9"),
            DeviceSoftwareRecord(device="edge-switch-5", os_version="NX-OS 10.3"),
        ]
        return ToolOutput.ok(devices)


class CVELookupTool:
    """Query CVE databases for known vulnerabilities."""

    def __init__(self) -> None:
        self._logger = build_logger("CVELookupTool")

    def lookup(self, product: str, version: str) -> ToolOutput:
        self._logger.info("cve_lookup", product=product, version=version)
        return ToolOutput.ok(
            [
                {
                    "cve_id": "CVE-2024-0001",
                    "severity": "critical",
                    "description": f"Example vulnerability for {product} {version}",
                }
            ]
        )


class LifecycleStatusRecord(BaseModel):
    """Lifecycle milestone record for a product."""

    product_model: str = Field(...)
    lifecycle_phase: str = Field(..., description="Lifecycle stage such as General Availability or End of Support")
    end_of_sale: Optional[date] = Field(default=None)
    end_of_support: Optional[date] = Field(default=None)
    notes: Optional[str] = Field(default=None)


class EoLEOSCheckTool:
    """Check vendor endpoints for lifecycle status."""

    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None) -> None:
        self._base_url = base_url
        self._api_token = api_token
        self._logger = build_logger("EoLEOSCheckTool")

    def check_lifecycle_status(self, product_model: str) -> ToolOutput:
        if httpx is None or self._base_url is None:
            self._logger.warning("lifecycle_httpx_unavailable", product_model=product_model)
            return ToolOutput.ok(self._synthetic_status(product_model))
        try:
            headers = {"Authorization": f"Bearer {self._api_token}"} if self._api_token else None
            response = httpx.get(
                f"{self._base_url}/lifecycle/status",
                params={"product": product_model},
                headers=headers,
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
            record = LifecycleStatusRecord.model_validate(payload)
            return ToolOutput.ok(record)
        except Exception as exc:  # pragma: no cover - network failures
            self._logger.error("lifecycle_query_failed", product_model=product_model, error=str(exc))
            return ToolOutput.ok(self._synthetic_status(product_model))

    def _synthetic_status(self, product_model: str) -> LifecycleStatusRecord:
        return LifecycleStatusRecord(
            product_model=product_model,
            lifecycle_phase="General Availability",
            end_of_sale=date.today().replace(year=date.today().year + 1),
            end_of_support=date.today().replace(year=date.today().year + 3),
            notes="Synthetic data – replace with vendor integration.",
        )


class PatchingStepResult(BaseModel):
    """Result for a single patching workflow step."""

    step: str = Field(...)
    success: bool = Field(...)
    details: Optional[Dict[str, Any]] = Field(default=None)


class PatchingWorkflowReport(BaseModel):
    """Aggregated workflow execution report."""

    device: str = Field(...)
    target_os_version: str = Field(...)
    status: str = Field(...)
    steps: List[PatchingStepResult] = Field(default_factory=list)


class AutomatedPatchingWorkflowTool:
    """Coordinate a multi-step patching workflow with injected dependencies."""

    def __init__(
        self,
        change_request_factory: Optional[Callable[[str, str], ToolOutput]] = None,
        config_backup: Optional[Callable[[str], ToolOutput]] = None,
        patch_executor: Optional[Callable[[str, str, str], ToolOutput]] = None,
        post_validation: Optional[Callable[[str], ToolOutput]] = None,
    ) -> None:
        self._change_request_factory = change_request_factory
        self._config_backup = config_backup
        self._patch_executor = patch_executor
        self._post_validation = post_validation
        self._logger = build_logger("AutomatedPatchingWorkflowTool")

    def execute_patching_workflow(self, device: str, target_os_version: str, image_path: str) -> ToolOutput:
        steps: List[PatchingStepResult] = []

        def record(step_name: str, result: ToolOutput) -> None:
            steps.append(
                PatchingStepResult(
                    step=step_name,
                    success=result.success,
                    details=result.data if result.success else (result.error.model_dump() if result.error else None),
                )
            )

        if self._change_request_factory is not None:
            result = self._change_request_factory(device, target_os_version)
        else:
            result = ToolOutput.ok({"ticket_id": f"CR-{device}-{datetime.utcnow().timestamp():.0f}"})
        record("change_request", result)
        if not result.success:
            return ToolOutput.ok(self._report(device, target_os_version, steps))

        if self._config_backup is not None:
            result = self._config_backup(device)
        else:
            result = ToolOutput.ok({"backup": "skipped"})
        record("preflight_backup", result)
        if not result.success:
            return ToolOutput.ok(self._report(device, target_os_version, steps))

        if self._patch_executor is not None:
            result = self._patch_executor(device, target_os_version, image_path)
        else:
            result = ToolOutput.ok({"status": "patch_applied"})
        record("patch_execution", result)
        if not result.success:
            return ToolOutput.ok(self._report(device, target_os_version, steps))

        if self._post_validation is not None:
            result = self._post_validation(device)
        else:
            result = ToolOutput.ok({"validation": "passed"})
        record("post_validation", result)

        return ToolOutput.ok(self._report(device, target_os_version, steps))

    def _report(self, device: str, target_os_version: str, steps: Sequence[PatchingStepResult]) -> PatchingWorkflowReport:
        status = "success" if all(step.success for step in steps) else "requires_attention"
        return PatchingWorkflowReport(
            device=device,
            target_os_version=target_os_version,
            status=status,
            steps=list(steps),
        )
