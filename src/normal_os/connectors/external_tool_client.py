"""Server-side client for the sandbox `external-tool` CLI.

All external connector traffic (Slack, Jira, Files, Gmail/Calendar, Finance,
OpticOdds, ...) is routed through the `external-tool` binary that the runtime
provides. This keeps credentials on the server side: the CLI resolves the
per-connector auth against the tools endpoint, so no secret ever has to live in
this repo or reach frontend code.

The client is intentionally thin and side-effect free on import. It shells out
to the binary, parses its JSON, and normalises the different failure shapes
(auth required, rate limited, connector error, transport error) into a single
`ExternalToolError` so callers can react uniformly.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DEFAULT_BINARY = "external-tool"
DEFAULT_TIMEOUT = 60

# Best-effort secret scrub for anything we log or surface. The CLI already
# redacts on its side; this is defence in depth for locally constructed
# messages (e.g. an argument echoed back in an error).
_SECRET_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"(?i)((?:api|access|refresh|secret)[_-]?(?:key|token)[\"']?\s*[=:]\s*)[^\s,;\"']+"),
)


def redact(text: str) -> str:
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub(lambda m: (m.group(1) if m.lastindex else "") + "[REDACTED]", out)
    return out


class ExternalToolError(RuntimeError):
    """Raised when an external-tool invocation fails.

    `kind` is a coarse machine-readable class so callers/tests can branch:
    ``auth_required`` | ``rate_limited`` | ``connector_error`` |
    ``transport_error`` | ``timeout`` | ``not_available``.
    """

    def __init__(self, kind: str, message: str, *, source_id: Optional[str] = None,
                 tool_name: Optional[str] = None, auth_url: Optional[str] = None):
        super().__init__(redact(message))
        self.kind = kind
        self.source_id = source_id
        self.tool_name = tool_name
        self.auth_url = auth_url


@dataclass
class ExternalToolClient:
    """Wrapper around the `external-tool` CLI.

    Args:
        binary: path/name of the CLI. Overridable via ``FUSION_EXTERNAL_TOOL_BIN``
            for tests or non-standard installs. No secret is ever read here.
        timeout: per-call subprocess timeout in seconds.
    """

    binary: str = ""
    timeout: int = DEFAULT_TIMEOUT

    def __post_init__(self) -> None:
        self.binary = (
            self.binary
            or os.getenv("FUSION_EXTERNAL_TOOL_BIN")
            or DEFAULT_BINARY
        )

    # -- availability -----------------------------------------------------
    def is_available(self) -> bool:
        """True if the CLI can be found on PATH (or as an explicit path)."""
        if os.path.isabs(self.binary):
            return os.path.exists(self.binary) and os.access(self.binary, os.X_OK)
        return shutil.which(self.binary) is not None

    # -- low level --------------------------------------------------------
    def _run(self, action: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        if not self.is_available():
            raise ExternalToolError(
                "not_available",
                f"external-tool binary '{self.binary}' not found on PATH",
            )
        cmd = [self.binary, action]
        if payload is not None:
            cmd.append(json.dumps(payload))
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExternalToolError("timeout", f"external-tool {action} timed out "
                                    f"after {self.timeout}s") from exc
        except OSError as exc:
            raise ExternalToolError("transport_error", str(exc)) from exc

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        if proc.returncode != 0:
            # The CLI puts structured errors on stderr as JSON when possible.
            self._raise_from_stderr(stderr or stdout, action)

        if not stdout:
            return None
        try:
            return json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            return stdout

    def _raise_from_stderr(self, text: str, action: str) -> None:
        parsed: Optional[Dict[str, Any]] = None
        # stderr often ends with a JSON object even if prefixed with 'error: '.
        for candidate in (text, text.split("error:", 1)[-1].strip()):
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    parsed = obj
                    break
            except (json.JSONDecodeError, ValueError):
                continue
        if parsed is not None:
            err = str(parsed.get("error", "")).lower()
            if parsed.get("error") == "auth_required" or "auth" in err:
                raise ExternalToolError(
                    "auth_required",
                    "connector requires authentication",
                    source_id=parsed.get("source_id"),
                    auth_url=parsed.get("auth_url"),
                )
            if "rate" in err and "limit" in err:
                raise ExternalToolError("rate_limited", parsed.get("error", text),
                                        source_id=parsed.get("source_id"))
            raise ExternalToolError(
                "connector_error",
                str(parsed.get("error", text)),
                source_id=parsed.get("source_id"),
                tool_name=parsed.get("tool_name"),
            )
        raise ExternalToolError("transport_error", text or f"external-tool {action} failed")

    # -- public API -------------------------------------------------------
    def list_sources(self) -> List[Dict[str, Any]]:
        result = self._run("list")
        return result if isinstance(result, list) else []

    def describe(self, source_id: str) -> Any:
        return self._run("describe", {"source_id": source_id})

    def call(self, source_id: str, tool_name: str,
             arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Invoke a connector tool. Returns parsed content on success.

        Some connectors return their own ``{"success": false, "error": ...}``
        envelope with a zero exit code; we surface that as a connector_error so
        callers get consistent behaviour.
        """
        result = self._run(
            "call",
            {"source_id": source_id, "tool_name": tool_name, "arguments": arguments or {}},
        )
        if isinstance(result, dict) and result.get("success") is False and "error" in result:
            err = result.get("error")
            msg = err.get("message") if isinstance(err, dict) else str(err)
            lowered = (msg or "").lower()
            kind = "auth_required" if ("auth" in lowered and "fail" in lowered) else "connector_error"
            raise ExternalToolError(kind, msg or "connector reported failure",
                                    source_id=source_id, tool_name=tool_name)
        return result
