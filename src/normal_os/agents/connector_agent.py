"""
ConnectorAgent example for normalOS

An agent that can autonomously use external connectors
(GitHub, Google Drive, PC-Bridge, Notion etc.).
"""

from typing import Any, Dict

from .base import BaseAgent


class ConnectorAgent(BaseAgent):
    """Agent that specializes in using external connectors."""

    def __init__(self, name: str = "ConnectorAgent"):
        super().__init__(name)

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        connector_name = task.get("connector")
        params = task.get("params", {})

        if not connector_name or not action:
            return {"error": "connector and action required"}

        connector = self.get_connector(connector_name)
        if not connector:
            return {"error": f"Connector {connector_name} not found"}

        result = await connector.execute(action, params)
        return {
            "agent": self.name,
            "connector": connector_name,
            "action": action,
            "result": result.model_dump()
        }
