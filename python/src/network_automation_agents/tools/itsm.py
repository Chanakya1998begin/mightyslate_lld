"""ITSM integration adapters."""

from abc import ABC, abstractmethod
from typing import Any, Optional

try:  # pragma: no cover - optional dependency during tests
    import httpx  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when httpx missing
    httpx = None  # type: ignore[assignment]
from pydantic import BaseModel, Field

from ..config import ITSMAdapterSettings
from ..logging import build_logger
from ..models import ToolOutput


class TicketPayload(BaseModel):
    summary: str = Field(..., description="Short description of the ticket.")
    description: str = Field(..., description="Detailed context for the issue.")
    urgency: Optional[str] = Field(default=None, description="ITSM-specific urgency field.")
    additional_fields: dict = Field(default_factory=dict, description="Adapter-specific fields.")


class ITSMAdapter(ABC):
    """Abstract base for ITSM API adapters."""

    def __init__(self, settings: ITSMAdapterSettings) -> None:
        self.settings = settings
        self._logger = build_logger(self.__class__.__name__)

    @abstractmethod
    def create_ticket(self, payload: TicketPayload) -> ToolOutput:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def update_ticket_status(self, ticket_id: str, status: str) -> ToolOutput:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def add_comment(self, ticket_id: str, comment: str) -> ToolOutput:  # pragma: no cover - interface
        raise NotImplementedError


class ServiceNowAdapter(ITSMAdapter):
    """Minimal ServiceNow adapter using httpx for REST operations."""

    def _client(self) -> Any:
        if httpx is None:  # pragma: no cover - executed only without dependency
            raise RuntimeError("httpx is required for ServiceNowAdapter")
        return httpx.Client(
            base_url=self.settings.instance_url,
            auth=(self.settings.username or "", self.settings.password_secret or ""),
        )

    def create_ticket(self, payload: TicketPayload) -> ToolOutput:
        if httpx is None:
            self._logger.warning("httpx_unavailable", action="create_ticket")
            return ToolOutput.fail("httpx dependency missing", details={"payload": payload.model_dump()})
        with self._client() as client:
            try:
                response = client.post("/api/now/table/incident", json=payload.model_dump())
                response.raise_for_status()
                ticket_id = response.json().get("result", {}).get("sys_id")
                return ToolOutput.ok({"ticket_id": ticket_id})
            except httpx.HTTPError as exc:  # pragma: no cover - network failure paths
                self._logger.error("servicenow_create_failed", error=str(exc))
                return ToolOutput.fail("Failed to create ServiceNow ticket", details={"exc": str(exc)})

    def update_ticket_status(self, ticket_id: str, status: str) -> ToolOutput:
        if httpx is None:
            self._logger.warning("httpx_unavailable", action="update_ticket_status")
            return ToolOutput.fail("httpx dependency missing", details={"ticket_id": ticket_id, "status": status})
        with self._client() as client:
            try:
                response = client.patch(
                    f"/api/now/table/incident/{ticket_id}",
                    json={"state": status},
                )
                response.raise_for_status()
                return ToolOutput.ok({"ticket_id": ticket_id, "status": status})
            except httpx.HTTPError as exc:  # pragma: no cover
                self._logger.error("servicenow_status_failed", error=str(exc))
                return ToolOutput.fail("Failed to update ServiceNow ticket", details={"exc": str(exc)})

    def add_comment(self, ticket_id: str, comment: str) -> ToolOutput:
        if httpx is None:
            self._logger.warning("httpx_unavailable", action="add_comment")
            return ToolOutput.fail("httpx dependency missing", details={"ticket_id": ticket_id})
        with self._client() as client:
            try:
                response = client.post(
                    f"/api/now/table/incident/{ticket_id}/comments",
                    json={"comment": comment},
                )
                response.raise_for_status()
                return ToolOutput.ok({"ticket_id": ticket_id})
            except httpx.HTTPError as exc:  # pragma: no cover
                self._logger.error("servicenow_comment_failed", error=str(exc))
                return ToolOutput.fail("Failed to add ServiceNow comment", details={"exc": str(exc)})


class JiraAdapter(ITSMAdapter):
    """Jira REST adapter using httpx for simplicity."""

    def _client(self) -> Any:
        if httpx is None:  # pragma: no cover
            raise RuntimeError("httpx is required for JiraAdapter")
        return httpx.Client(
            base_url=self.settings.instance_url,
            auth=(self.settings.username or "", self.settings.password_secret or ""),
        )

    def create_ticket(self, payload: TicketPayload) -> ToolOutput:
        if httpx is None:
            self._logger.warning("httpx_unavailable", action="create_ticket")
            return ToolOutput.fail("httpx dependency missing", details={"payload": payload.model_dump()})
        with self._client() as client:
            try:
                data = {
                    "fields": {
                        "summary": payload.summary,
                        "description": payload.description,
                        **payload.additional_fields,
                    }
                }
                response = client.post("/rest/api/3/issue", json=data)
                response.raise_for_status()
                return ToolOutput.ok(response.json())
            except httpx.HTTPError as exc:  # pragma: no cover
                self._logger.error("jira_create_failed", error=str(exc))
                return ToolOutput.fail("Failed to create Jira issue", details={"exc": str(exc)})

    def update_ticket_status(self, ticket_id: str, status: str) -> ToolOutput:
        if httpx is None:
            self._logger.warning("httpx_unavailable", action="update_ticket_status")
            return ToolOutput.fail("httpx dependency missing", details={"ticket_id": ticket_id, "status": status})
        with self._client() as client:
            try:
                transition = {"transition": {"id": status}}
                response = client.post(f"/rest/api/3/issue/{ticket_id}/transitions", json=transition)
                response.raise_for_status()
                return ToolOutput.ok({"ticket_id": ticket_id, "status": status})
            except httpx.HTTPError as exc:  # pragma: no cover
                self._logger.error("jira_transition_failed", error=str(exc))
                return ToolOutput.fail("Failed to transition Jira issue", details={"exc": str(exc)})

    def add_comment(self, ticket_id: str, comment: str) -> ToolOutput:
        if httpx is None:
            self._logger.warning("httpx_unavailable", action="add_comment")
            return ToolOutput.fail("httpx dependency missing", details={"ticket_id": ticket_id})
        with self._client() as client:
            try:
                response = client.post(
                    f"/rest/api/3/issue/{ticket_id}/comment",
                    json={"body": comment},
                )
                response.raise_for_status()
                return ToolOutput.ok({"ticket_id": ticket_id})
            except httpx.HTTPError as exc:  # pragma: no cover
                self._logger.error("jira_comment_failed", error=str(exc))
                return ToolOutput.fail("Failed to add Jira comment", details={"exc": str(exc)})


class ITSMIntegrationTool:
    """Factory that selects an ITSM adapter based on settings."""

    def __init__(self, settings: ITSMAdapterSettings) -> None:
        self.settings = settings
        self._adapter = self._load_adapter(settings)

    def _load_adapter(self, settings: ITSMAdapterSettings) -> ITSMAdapter:
        provider = (settings.provider or "").lower()
        if provider == "jira":
            return JiraAdapter(settings)
        return ServiceNowAdapter(settings)

    def create_ticket(self, payload: TicketPayload) -> ToolOutput:
        return self._adapter.create_ticket(payload)

    def update_ticket_status(self, ticket_id: str, status: str) -> ToolOutput:
        return self._adapter.update_ticket_status(ticket_id, status)

    def add_comment(self, ticket_id: str, comment: str) -> ToolOutput:
        return self._adapter.add_comment(ticket_id, comment)
