"""Configuration management tooling implementations."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional, Sequence

import difflib
import json
import re

try:  # pragma: no cover - optional dependency
    from git import GitCommandError, Repo  # type: ignore[import-not-found]
    from git.exc import InvalidGitRepositoryError, NoSuchPathError  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback when GitPython missing
    GitCommandError = InvalidGitRepositoryError = NoSuchPathError = Exception  # type: ignore[assignment]
    Repo = None  # type: ignore[assignment]

from pydantic import BaseModel, Field

from ..logging import build_logger
from ..models import ToolOutput


class ConfigBackupResult(BaseModel):
    """Outcome of a configuration backup operation."""

    device: str = Field(...)
    path: str = Field(..., description="Filesystem path where the configuration snapshot is stored.")
    commit_hash: Optional[str] = Field(default=None, description="Git commit hash if versioned.")


class VersionControlTool:
    """Manage a Git-backed configuration repository with graceful fallbacks."""

    def __init__(self, repo_path: Path | str, branch: Optional[str] = None) -> None:
        self._repo_path = Path(repo_path)
        self._branch = branch
        self._logger = build_logger("VersionControlTool")
        self._repo = self._try_load_repo()

    def _try_load_repo(self):
        if Repo is None:
            self._logger.warning("gitpython_unavailable", repo=str(self._repo_path))
            return None
        try:
            repo = Repo(self._repo_path)
            if self._branch and repo.active_branch.name != self._branch:
                try:
                    repo.git.checkout(self._branch)
                except GitCommandError as exc:  # pragma: no cover - depends on git state
                    self._logger.warning("git_checkout_failed", branch=self._branch, error=str(exc))
            return repo
        except (InvalidGitRepositoryError, NoSuchPathError):  # pragma: no cover - environment specific
            self._logger.warning("git_repo_missing", path=str(self._repo_path))
            return None

    def commit_config(self, device: str, config_content: str, commit_message: str) -> ToolOutput:
        config_dir = self._repo_path / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        file_path = config_dir / f"{device}.cfg"
        file_path.write_text(config_content, encoding="utf-8")
        commit_hash: Optional[str] = None

        if self._repo is not None:
            rel_path = str(file_path.relative_to(self._repo.working_tree_dir)) if self._repo.working_tree_dir else str(file_path)
            try:
                self._repo.index.add([rel_path])
                if self._repo.is_dirty(index=True, working_tree=False, untracked_files=True):
                    commit = self._repo.index.commit(commit_message)
                    commit_hash = commit.hexsha
                    self._logger.info("git_commit", commit=commit_hash, device=device)
                else:
                    self._logger.info("git_no_changes", device=device)
            except GitCommandError as exc:  # pragma: no cover - git command failures
                self._logger.error("git_commit_failed", error=str(exc))

        result = ConfigBackupResult(device=device, path=str(file_path), commit_hash=commit_hash)
        return ToolOutput.ok(result)


class ConfigBackupTool:
    """Coordinate configuration retrieval and versioning."""

    def __init__(
        self,
        config_fetcher: Callable[[str], ToolOutput | str],
        version_control: VersionControlTool,
        serializer: Optional[Callable[[Any], str]] = None,
    ) -> None:
        self._config_fetcher = config_fetcher
        self._version_control = version_control
        self._serializer = serializer
        self._logger = build_logger("ConfigBackupTool")

    def backup_config(self, device: str) -> ToolOutput:
        fetched = self._config_fetcher(device)
        if isinstance(fetched, ToolOutput):
            if not fetched.success:
                return fetched
            config_content = fetched.data
        else:
            config_content = fetched
        if config_content is None:
            return ToolOutput.fail("No configuration content returned", details={"device": device})
        if not isinstance(config_content, str):
            if self._serializer is None:
                config_content = json.dumps(config_content, indent=2, sort_keys=True)
            else:
                config_content = self._serializer(config_content)
        commit_message = f"AUTOBACKUP: Configuration backup for {device} @ {datetime.utcnow().isoformat()}Z"
        self._logger.info("backup_config", device=device)
        return self._version_control.commit_config(device, config_content, commit_message)


class ConfigDriftOutput(BaseModel):
    """Structured result of a drift detection run."""

    device: str = Field(...)
    is_drifted: bool = Field(...)
    diff: Optional[str] = Field(default=None, description="Unified diff when drift detected.")


class ConfigDriftDetectionTool:
    """Compare live configurations to approved baselines."""

    def __init__(
        self,
        running_config_fetcher: Callable[[str], str | ToolOutput],
        baseline_loader: Callable[[str], str | ToolOutput],
        ignore_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        self._running_fetcher = running_config_fetcher
        self._baseline_loader = baseline_loader
        self._ignore_patterns = [re.compile(pat) for pat in ignore_patterns or []]
        self._logger = build_logger("ConfigDriftDetectionTool")

    def detect_drift(self, device: str) -> ToolOutput:
        running = self._resolve(self._running_fetcher(device), "running_config")
        if not running.success:
            return running
        baseline = self._resolve(self._baseline_loader(device), "baseline_config")
        if not baseline.success:
            return baseline

        running_lines = self._filter_lines(str(running.data).splitlines())
        baseline_lines = self._filter_lines(str(baseline.data).splitlines())
        diff_lines = list(
            difflib.unified_diff(
                baseline_lines,
                running_lines,
                fromfile="baseline",
                tofile="running",
                lineterm="",
            )
        )
        is_drifted = any(line.startswith(('+', '-')) and not line.startswith(('+++', '---')) for line in diff_lines)
        result = ConfigDriftOutput(
            device=device,
            is_drifted=is_drifted,
            diff="\n".join(diff_lines) if is_drifted else None,
        )
        self._logger.info("config_drift", device=device, drift=is_drifted)
        return ToolOutput.ok(result)

    def _resolve(self, value: str | ToolOutput, label: str) -> ToolOutput:
        if isinstance(value, ToolOutput):
            return value
        if value is None:
            return ToolOutput.fail(f"{label} not available")
        return ToolOutput.ok(value)

    def _filter_lines(self, lines: Iterable[str]) -> List[str]:
        if not self._ignore_patterns:
            return list(lines)
        filtered = []
        for line in lines:
            if any(pattern.search(line) for pattern in self._ignore_patterns):
                continue
            filtered.append(line)
        return filtered


class ComplianceRule(BaseModel):
    """Definition of a compliance rule."""

    rule_id: str = Field(...)
    description: str = Field(...)
    pattern: str = Field(..., description="Regex pattern to evaluate against the configuration text.")
    mode: str = Field(..., description="Either 'required' or 'forbidden'.")


class ComplianceViolation(BaseModel):
    """Details for a single compliance violation."""

    rule_id: str = Field(...)
    rule_description: str = Field(...)
    violating_line: Optional[str] = Field(default=None)
    violation_type: str = Field(..., description="missing_required or found_forbidden")


class ComplianceReport(BaseModel):
    """Aggregated compliance findings."""

    policy_name: str = Field(...)
    is_compliant: bool = Field(...)
    violations: List[ComplianceViolation] = Field(default_factory=list)


class ComplianceAuditTool:
    """Evaluate configurations against policy rule sets."""

    def __init__(
        self,
        policy_rules: Optional[dict[str, Sequence[ComplianceRule]]] = None,
        rule_loader: Optional[Callable[[str], Sequence[ComplianceRule]]] = None,
    ) -> None:
        self._policy_rules = policy_rules or {}
        self._rule_loader = rule_loader
        self._logger = build_logger("ComplianceAuditTool")

    def audit_config(
        self,
        config_content: str,
        policy_name: str,
        extra_rules: Optional[Sequence[ComplianceRule]] = None,
    ) -> ToolOutput:
        rules = list(self._policy_rules.get(policy_name, []))
        if not rules and self._rule_loader:
            try:
                rules.extend(self._rule_loader(policy_name))
            except Exception as exc:  # pragma: no cover - loader implementation specific
                self._logger.error("rule_loader_failed", policy=policy_name, error=str(exc))
                return ToolOutput.fail("Failed to load compliance rules", details={"policy": policy_name})
        if extra_rules:
            rules.extend(extra_rules)
        if not rules:
            return ToolOutput.fail("No compliance rules defined", details={"policy": policy_name})

        violations: List[ComplianceViolation] = []
        for rule in rules:
            pattern = re.compile(rule.pattern, re.MULTILINE)
            matches = list(pattern.finditer(config_content))
            if rule.mode == "required" and not matches:
                violations.append(
                    ComplianceViolation(
                        rule_id=rule.rule_id,
                        rule_description=rule.description,
                        violation_type="missing_required",
                    )
                )
            elif rule.mode == "forbidden" and matches:
                for match in matches:
                    violations.append(
                        ComplianceViolation(
                            rule_id=rule.rule_id,
                            rule_description=rule.description,
                            violating_line=match.group(0),
                            violation_type="found_forbidden",
                        )
                    )

        report = ComplianceReport(policy_name=policy_name, is_compliant=not violations, violations=violations)
        self._logger.info("compliance_audit", policy=policy_name, compliant=report.is_compliant)
        return ToolOutput.ok(report)


__all__ = [
    "VersionControlTool",
    "ConfigBackupTool",
    "ConfigBackupResult",
    "ConfigDriftDetectionTool",
    "ConfigDriftOutput",
    "ComplianceAuditTool",
    "ComplianceRule",
    "ComplianceViolation",
    "ComplianceReport",
]
