"""Declarative specs for the externally connected services.

Each :class:`ConnectorSpec` describes one connected service: its runtime
``source_id``, transport, the tools it exposes (with required arguments and a
read-only/mutating classification), and a single *safe* read-only probe used
for health checks. Startup and health checks only ever invoke the probe, never
a mutating tool, so bringing the OS up cannot cause an irreversible action.

Transports:
    ``external_tool`` — routed through the `external-tool` CLI.
    ``gh_cli``        — GitHub, routed through the authenticated `gh`/`git` CLI
                        per project policy (never the raw connector).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

TRANSPORT_EXTERNAL_TOOL = "external_tool"
TRANSPORT_GH_CLI = "gh_cli"


@dataclass(frozen=True)
class ToolCapability:
    name: str
    description: str = ""
    required: List[str] = field(default_factory=list)
    mutating: bool = False  # True => refused during health checks / read-only mode


@dataclass(frozen=True)
class HealthProbe:
    """A safe, read-only call used to verify a connector is live."""

    tool_name: str
    arguments: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ConnectorSpec:
    name: str  # stable local key, e.g. "slack"
    source_id: str  # runtime source id, e.g. "slack_direct"
    display_name: str
    transport: str
    description: str
    capabilities: List[ToolCapability]
    health: Optional[HealthProbe] = None

    def capability(self, tool_name: str) -> Optional[ToolCapability]:
        for cap in self.capabilities:
            if cap.name == tool_name:
                return cap
        return None

    def read_only_tools(self) -> List[str]:
        return [c.name for c in self.capabilities if not c.mutating]


CONNECTOR_SPECS: Dict[str, ConnectorSpec] = {
    "slack": ConnectorSpec(
        name="slack",
        source_id="slack_direct",
        display_name="Slack",
        transport=TRANSPORT_EXTERNAL_TOOL,
        description="Slack workspace search and messaging",
        health=HealthProbe("slack_search_channels",
                           {"query": "general", "limit": 1, "response_format": "concise"}),
        capabilities=[
            ToolCapability("slack_search_channels", "Search channels", ["query"]),
            ToolCapability("slack_search_public", "Search public messages", ["query"]),
            ToolCapability("slack_search_public_and_private",
                           "Search public+private messages", ["query"]),
            ToolCapability("slack_search_users", "Search users", ["query"]),
            ToolCapability("slack_read_channel", "Read a channel", ["channel_id"]),
            ToolCapability("slack_read_thread", "Read a thread",
                           ["channel_id", "message_ts"]),
            ToolCapability("slack_read_user_profile", "Read a user profile", []),
            ToolCapability("slack_read_canvas", "Read a canvas", ["canvas_id"]),
            ToolCapability("slack_send_message", "Post a message",
                           ["channel_id", "message"], mutating=True),
            ToolCapability("slack_send_message_draft", "Create a draft message",
                           ["channel_id", "message"], mutating=True),
            ToolCapability("slack_schedule_message", "Schedule a message",
                           ["channel_id", "message", "post_at"], mutating=True),
            ToolCapability("slack_create_canvas", "Create a canvas",
                           ["title", "content"], mutating=True),
            ToolCapability("slack_update_canvas", "Update a canvas",
                           ["canvas_id", "action", "content"], mutating=True),
        ],
    ),
    "jira": ConnectorSpec(
        name="jira",
        source_id="jira_mcp_merge",
        display_name="Jira",
        transport=TRANSPORT_EXTERNAL_TOOL,
        description="Jira issues, projects, boards and sprints",
        health=HealthProbe("jira__get_current_user", {"expand": None}),
        capabilities=[
            ToolCapability("jira__get_current_user", "Current user", ["expand"]),
            ToolCapability("jira__validate_credential", "Validate credentials", []),
            ToolCapability("jira__search_issues", "Search issues (JQL)", ["input"]),
            ToolCapability("jira__get_issue", "Get an issue",
                           ["issue_key", "expand", "fields"]),
            ToolCapability("jira__get_projects", "List projects", []),
            ToolCapability("jira__get_project", "Get a project", ["project_key", "expand"]),
            ToolCapability("jira__list_statuses", "List statuses", []),
            ToolCapability("jira__get_priorities", "List priorities", []),
            ToolCapability("jira__create_issue", "Create an issue",
                           ["input", "auto_discover"], mutating=True),
            ToolCapability("jira__update_issue", "Update an issue", ["input"], mutating=True),
            ToolCapability("jira__delete_issue", "Delete an issue",
                           ["issue_key", "delete_subtasks"], mutating=True),
            ToolCapability("jira__add_comment", "Add a comment", ["input"], mutating=True),
            ToolCapability("jira__transition_issue", "Transition an issue",
                           ["input"], mutating=True),
        ],
    ),
    "files": ConnectorSpec(
        name="files",
        source_id="files",
        display_name="Files (OneDrive/SharePoint/Google Drive)",
        transport=TRANSPORT_EXTERNAL_TOOL,
        description="Unified file search across connected drives",
        health=HealthProbe("search_files_v2",
                           {"queries": ["fusion hero"], "retrieval_mode": "SEARCH",
                            "context_budget": "SHORT"}),
        capabilities=[
            ToolCapability("search_files_v2", "Unified file search", []),
        ],
    ),
    "gcal": ConnectorSpec(
        name="gcal",
        source_id="gcal",
        display_name="Gmail with Calendar",
        transport=TRANSPORT_EXTERNAL_TOOL,
        description="Gmail search and Google Calendar",
        health=HealthProbe(
            "search_calendar",
            {"start_date": "2026-01-01", "end_date": "2026-01-02", "queries": ["health"]},
        ),
        capabilities=[
            ToolCapability("search_email", "Search email", ["queries"]),
            ToolCapability("search_calendar", "Search calendar",
                           ["start_date", "end_date", "queries"]),
            ToolCapability("draft_email", "Draft an email",
                           ["subject", "body"], mutating=True),
            ToolCapability("send_email", "Send an email", ["action"], mutating=True),
            ToolCapability("update_calendar", "Modify calendar",
                           ["create_actions", "delete_actions", "update_actions"],
                           mutating=True),
        ],
    ),
    "github": ConnectorSpec(
        name="github",
        source_id="github_mcp_direct",
        display_name="GitHub",
        transport=TRANSPORT_GH_CLI,
        description="GitHub via authenticated gh/git CLI (per project policy)",
        health=HealthProbe("get_me", {}),
        capabilities=[
            ToolCapability("get_me", "Authenticated user (gh api user)", []),
            ToolCapability("list_repos", "List repositories", []),
            ToolCapability("get_repo", "Get a repository", ["owner", "repo"]),
            ToolCapability("list_pull_requests", "List pull requests", ["owner", "repo"]),
        ],
    ),
    "finance": ConnectorSpec(
        name="finance",
        source_id="finance",
        display_name="Realtime Finance Data",
        transport=TRANSPORT_EXTERNAL_TOOL,
        description="Realtime market data, quotes and sentiment",
        health=HealthProbe("finance_market_sentiment", {}),
        capabilities=[
            ToolCapability("finance_market_sentiment", "Market sentiment", []),
            ToolCapability("finance_quotes", "Quotes", ["ticker_symbols"]),
            ToolCapability("finance_tickers_lookup", "Ticker lookup", ["queries"]),
            ToolCapability("finance_company_profile", "Company profile", ["ticker_symbols"]),
            ToolCapability("finance_market_gainers", "Top gainers", []),
            ToolCapability("finance_market_losers", "Top losers", []),
            ToolCapability("finance_macro_snapshot", "Macro snapshot", []),
        ],
    ),
    "opticodds": ConnectorSpec(
        name="opticodds",
        source_id="opticodds",
        display_name="OpticOdds",
        transport=TRANSPORT_EXTERNAL_TOOL,
        description="OpticOdds sports/odds API (generic GET/POST passthrough)",
        health=HealthProbe("opticodds", {"path": "/sports", "method": "GET"}),
        capabilities=[
            # A single passthrough tool; GET is read-only, POST may mutate, so we
            # treat the generic tool as read-only and gate POST at the adapter.
            ToolCapability("opticodds", "Generic OpticOdds v3 request", ["path"]),
        ],
    ),
}


def all_specs() -> List[ConnectorSpec]:
    return list(CONNECTOR_SPECS.values())
