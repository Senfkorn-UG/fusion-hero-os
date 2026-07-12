#!/usr/bin/env python3
"""
Fusion Hero OS - Unified Launcher v7.5
======================================

Central entry point for the entire Fusion Hero OS project.

Responsibilities:
- Start the current active system (C Bridge + optional Dashboard)
- Provide awareness and access to archived beta versions
- Clean process management and shutdown
- Extensible foundation

Usage:
    python start_fusion_hero.py
    python start_fusion_hero.py --with-dashboard
    python start_fusion_hero.py --list-versions
"""

import os
import sys
import signal
import subprocess
import time
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# =============================================================================
# Paths
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.resolve()
BRIDGE_DIR = PROJECT_ROOT / "kernel" / "bridge"
C_SERVER_SRC = BRIDGE_DIR / "fhos_ipc_server.c"
C_SERVER_BIN = BRIDGE_DIR / "fhos_ipc_server"
DASHBOARD_DIR = PROJECT_ROOT / "03_Code" / "Dashboard"
DASHBOARD_SCRIPT = DASHBOARD_DIR / "heroic_core_gui.py"
ARCHIVE_DIR = PROJECT_ROOT / "06_Master_Archive"
SOCKET_PATH = "/tmp/fusion_hero_ipc.sock"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("FusionHeroOS")


class ProcessManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []

    def add(self, process: subprocess.Popen):
        if process:
            self.processes.append(process)

    def shutdown_all(self):
        logger.info("Shutting down all components...")
        for proc in reversed(self.processes):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self.processes.clear()
        logger.info("All components stopped cleanly.")


def compile_c_server() -> bool:
    if C_SERVER_BIN.exists() and C_SERVER_BIN.stat().st_mtime >= C_SERVER_SRC.stat().st_mtime:
        return True

    logger.info("Compiling C IPC Bridge server...")
    cmd = ["gcc", "-Wall", "-Wextra", "-O2", "-o", str(C_SERVER_BIN), str(C_SERVER_SRC)]
    try:
        subprocess.run(cmd, cwd=BRIDGE_DIR, check=True, capture_output=True, text=True)
        logger.info("C server compiled successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to compile C server.")
        if e.stderr:
            logger.error(e.stderr)
        return False


def start_bridge_server(manager: ProcessManager) -> Optional[subprocess.Popen]:
    if not C_SERVER_BIN.exists():
        return None

    if os.path.exists(SOCKET_PATH):
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass

    logger.info("Starting C IPC Bridge server...")
    proc = subprocess.Popen(
        [str(C_SERVER_BIN)],
        cwd=BRIDGE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    manager.add(proc)
    time.sleep(0.7)
    logger.info(f"C IPC Bridge active (PID: {proc.pid})")
    return proc


def start_dashboard(manager: ProcessManager) -> Optional[subprocess.Popen]:
    if not DASHBOARD_SCRIPT.exists():
        logger.warning("Dashboard script not found. Skipping.")
        return None

    logger.info("Starting Heroic Dashboard...")
    try:
        proc = subprocess.Popen([sys.executable, str(DASHBOARD_SCRIPT)], cwd=DASHBOARD_DIR)
        manager.add(proc)
        logger.info(f"Dashboard started (PID: {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Failed to start Dashboard: {e}")
        return None


def list_archived_versions():
    print("\n\U0001F4DC Available Archived Beta Versions / Historical States:\n")
    if not ARCHIVE_DIR.exists():
        print("No archive directory found.")
        return

    items = sorted([p for p in ARCHIVE_DIR.iterdir() if p.is_dir() or p.suffix in (".md", ".pdf")])
    for item in items[:30]:
        print(f"  - {item.name}")
    if len(items) > 30:
        print(f"  ... and {len(items) - 30} more items")
    print("\nThese versions remain part of the project history.\n")


def main():
    parser = argparse.ArgumentParser(description="Fusion Hero OS Unified Launcher")
    parser.add_argument("--bridge-only", action="store_true")
    parser.add_argument("--with-dashboard", action="store_true")
    parser.add_argument("--list-versions", action="store_true")
    args = parser.parse_args()

    if args.list_versions:
        list_archived_versions()
        return

    print("\n" + "=" * 64)
    print("   \u2694️ FUSION HERO OS - LAUNCHER v7.5")
    print("   ALTE_Frau_95g Heroic Core | Includes all Beta History")
    print("=" * 64 + "\n")

    manager = ProcessManager()

    def shutdown_handler(sig, frame):
        manager.shutdown_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    if not compile_c_server():
        logger.critical("Cannot proceed without C Bridge.")
        sys.exit(1)

    bridge = start_bridge_server(manager)
    if not bridge:
        manager.shutdown_all()
        sys.exit(1)

    if args.with_dashboard:
        start_dashboard(manager)

    try:
        if args.bridge_only:
            logger.info("Bridge-only mode active. Press Ctrl+C to stop.")
            for line in bridge.stdout:
                print(line, end="")
        else:
            logger.info("Fusion Hero OS core environment is running.")
            logger.info("All previous beta versions remain integrated in the archive.")
            logger.info("\nPress Ctrl+C to shut down.\n")

            while True:
                time.sleep(1)
                if bridge.poll() is not None:
                    logger.error("Bridge server exited unexpectedly.")
                    break

    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown_all()
        print("\nFusion Hero OS stopped cleanly.\n")


if __name__ == "__main__":
    main()
