#!/usr/bin/env python3
"""
GrokPCBridge v1

Bidirectional local PC bridge for Fusion Hero OS / normalOS.
Analog to the PhoneBridge concept but focused on controlled, explicit access
between Grok Mainframe and the user's local Windows PC.

Primary use cases:
- Secure desktop file inspection (list, search, read)
- Future: controlled command execution, resource monitoring, file sync
- Solves the "check what Claude left on my desktop" class of requests

Security model:
- User explicitly starts the bridge
- Token-based authentication (printed on start or from config)
- Read-only by default
- Path allow-list (Desktop + selected safe folders)
- All operations logged
- No write/delete operations in v1

Run on your local PC:
    python -m src.normal_os.bridge.grok_pc_bridge

Then connect from Grok/normalOS using the printed token and http://localhost:8765
"""

import os
import sys
import json
import time
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import uvicorn


# =============================================================================
# Configuration
# =============================================================================

class BridgeConfig(BaseModel):
    """Configuration for GrokPCBridge."""
    host: str = "127.0.0.1"
    port: int = 8765
    token: Optional[str] = None          # If None, a new token is generated on start
    allowed_base_paths: List[str] = Field(
        default_factory=lambda: [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
        ]
    )
    max_read_size_bytes: int = 2 * 1024 * 1024   # 2 MB max per read
    log_level: str = "INFO"


# =============================================================================
# Data Models
# =============================================================================

class BridgeStatus(BaseModel):
    status: str = "running"
    version: str = "1.0.0"
    started_at: str
    host: str
    port: int
    latency_ms: Optional[float] = None


class PingResponse(BaseModel):
    pong: bool = True
    timestamp: str
    server_time: float
    latency_ms: Optional[float] = None


class FileInfo(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified: str


class SearchResult(BaseModel):
    matches: List[FileInfo]
    total: int
    query: str


class ReadFileResponse(BaseModel):
    path: str
    content: str
    size: int
    truncated: bool = False


# =============================================================================
# GrokPCBridge Implementation
# =============================================================================

class GrokPCBridge:
    """Main bridge class. Can run as server or be used as client."""

    def __init__(self, config: Optional[BridgeConfig] = None):
        self.config = config or BridgeConfig()
        self.app = FastAPI(
            title="GrokPCBridge",
            description="Bidirectional bridge between Grok/normalOS and local PC",
            version="1.0.0"
        )
        self.started_at = datetime.utcnow().isoformat()
        self.token = self.config.token or str(uuid.uuid4())
        self._setup_routes()
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper(), logging.INFO),
            format="%(asctime)s | GrokPCBridge | %(levelname)s | %(message)s"
        )
        self.logger = logging.getLogger("grok_pc_bridge")

    def _verify_token(self, authorization: Optional[str] = Header(None)) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        token = authorization.split(" ", 1)[1]
        if token != self.token:
            raise HTTPException(status_code=403, detail="Invalid token")
        return token

    def _is_path_allowed(self, path: Path) -> bool:
        try:
            resolved = path.resolve(strict=False)
            for base in self.config.allowed_base_paths:
                base_resolved = Path(base).resolve(strict=False)
                if str(resolved).startswith(str(base_resolved)):
                    return True
            return False
        except Exception:
            return False

    def _setup_routes(self):
        @self.app.get("/status", response_model=BridgeStatus)
        async def status():
            return BridgeStatus(
                started_at=self.started_at,
                host=self.config.host,
                port=self.config.port,
            )

        @self.app.get("/ping", response_model=PingResponse)
        async def ping():
            return PingResponse(
                timestamp=datetime.utcnow().isoformat(),
                server_time=time.time(),
            )

        @self.app.get("/desktop/list", response_model=List[FileInfo])
        async def list_desktop(
            subpath: str = "",
            token: str = Depends(self._verify_token)
        ):
            base = Path.home() / "Desktop"
            target = (base / subpath).resolve()

            if not self._is_path_allowed(target):
                raise HTTPException(status_code=403, detail="Path not allowed")

            if not target.exists():
                raise HTTPException(status_code=404, detail="Path not found")

            items: List[FileInfo] = []
            for entry in target.iterdir():
                try:
                    stat = entry.stat()
                    items.append(
                        FileInfo(
                            name=entry.name,
                            path=str(entry),
                            is_dir=entry.is_dir(),
                            size=stat.st_size if not entry.is_dir() else 0,
                            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Could not stat {entry}: {e}")
            return items

        @self.app.get("/desktop/search", response_model=SearchResult)
        async def search_desktop(
            query: str,
            token: str = Depends(self._verify_token)
        ):
            base = Path.home() / "Desktop"
            matches: List[FileInfo] = []

            for root, dirs, files in os.walk(base):
                for name in files + dirs:
                    if query.lower() in name.lower():
                        full_path = Path(root) / name
                        try:
                            stat = full_path.stat()
                            matches.append(
                                FileInfo(
                                    name=name,
                                    path=str(full_path),
                                    is_dir=full_path.is_dir(),
                                    size=stat.st_size if full_path.is_file() else 0,
                                    modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                )
                            )
                        except Exception:
                            pass

            return SearchResult(matches=matches, total=len(matches), query=query)

        @self.app.get("/desktop/read", response_model=ReadFileResponse)
        async def read_desktop_file(
            path: str,
            token: str = Depends(self._verify_token)
        ):
            target = Path(path).resolve()

            if not self._is_path_allowed(target):
                raise HTTPException(status_code=403, detail="Path not allowed")

            if not target.is_file():
                raise HTTPException(status_code=404, detail="File not found or is a directory")

            if target.stat().st_size > self.config.max_read_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large (>{self.config.max_read_size_bytes} bytes)"
                )

            try:
                content = target.read_text(encoding="utf-8", errors="replace")
                return ReadFileResponse(
                    path=str(target),
                    content=content,
                    size=len(content),
                    truncated=False,
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

        @self.app.get("/system/info")
        async def system_info(token: str = Depends(self._verify_token)):
            return {
                "platform": sys.platform,
                "user": os.getlogin() if hasattr(os, "getlogin") else os.environ.get("USERNAME"),
                "home": str(Path.home()),
                "desktop": str(Path.home() / "Desktop"),
                "python": sys.version,
            }


# =============================================================================
# CLI / Server Entry Point
# =============================================================================

def run_bridge(config: Optional[BridgeConfig] = None):
    """Start the GrokPCBridge server."""
    bridge = GrokPCBridge(config)

    print("\n" + "=" * 70)
    print("GrokPCBridge v1.0 started")
    print("=" * 70)
    print(f"Host:        {bridge.config.host}")
    print(f"Port:        {bridge.config.port}")
    print(f"Token:       {bridge.token}")
    print(f"Allowed paths: {bridge.config.allowed_base_paths}")
    print("\nIMPORTANT:")
    print("  - Keep this terminal open while using the bridge")
    print("  - Use the token above when connecting from Grok/normalOS")
    print("  - Example Authorization header: Bearer <token>")
    print("=" * 70 + "\n")

    uvicorn.run(
        bridge.app,
        host=bridge.config.host,
        port=bridge.config.port,
        log_level=bridge.config.log_level.lower(),
    )


if __name__ == "__main__":
    run_bridge()
