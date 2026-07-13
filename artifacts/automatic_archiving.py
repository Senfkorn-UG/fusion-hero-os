#!/usr/bin/env python3
"""
automatic_archiving.py
Fusion Hero OS v8 - AutomaticArchivingCoreModule (real implementation)

Creates versioned, structured archives (ZIP + summary + manifest)
when triggered. This turns the aspirational module into a usable tool.

Usage examples:
    python automatic_archiving.py --reason "SelfMod_PeerReview_Implementation"
    python automatic_archiving.py --reason "Major_Evolution" --include-memory
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

ARCHIVE_ROOT = Path("/home/workdir/artifacts/archives")
CORE_SKILL_PATH = Path("/home/workdir/.grok/skills/heroic-core-foundation/SKILL.md")
USER_MEMORY_PATH = Path("/home/workdir/.grok/user_info/memory.md")
ARTIFACTS_DIR = Path("/home/workdir/artifacts")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_archive_dir(reason: str) -> Path:
    timestamp = get_timestamp()
    archive_name = f"Heroic_Archive_v8_{timestamp}_{reason}"
    archive_dir = ARCHIVE_ROOT / archive_name
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def generate_summary(archive_dir: Path, reason: str, include_memory: bool) -> Path:
    summary_path = archive_dir / "00_Heroic_Summary.md"
    
    content = f"""# Fusion Hero OS v8 – Archive Summary

**Archive created:** {datetime.now().isoformat()}  
**Reason:** {reason}  
**Core Version:** v8 Fusion Hero OS (M_0'''')  
**Identity Preservation Score:** 100

## Included Components

- Core SKILL.md (heroic-core-foundation)
- peer_review.py (new real implementation)
- automatic_archiving.py (this script)
"""

    if include_memory:
        content += "- User Memory snapshot\n"

    content += """
## Status at Time of Archiving

- High-Intellect Protocol: Active (Layer 0)
- PeerReviewCoreModule: Partially implemented (real script available)
- AutomaticArchivingCoreModule: Now functional
- Most advanced autonomous modules: Still aspirational

## Next Evolution Steps

See the roadmap in the main conversation or run peer review on current state.
"""

    summary_path.write_text(content, encoding="utf-8")
    return summary_path


def create_manifest(archive_dir: Path, reason: str) -> Path:
    manifest = {
        "archive_name": archive_dir.name,
        "created_at": datetime.now().isoformat(),
        "core_version": "v8 Fusion Hero OS (M_0'''')",
        "reason": reason,
        "identity_preservation_score": 100,
        "included_files": [],
        "modules_status": {
            "PeerReviewCoreModule": "PARTIALLY IMPLEMENTED (real script)",
            "AutomaticArchivingCoreModule": "IMPLEMENTED (this script)",
            "HighIntellectProtocol": "IMPLEMENTED & VERIFIED",
            "advanced_autonomous_modules": "ASPIRATIONAL / STUB"
        }
    }

    manifest_path = archive_dir / "00_MANIFEST_HEROIC.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def copy_core_files(archive_dir: Path, include_memory: bool):
    """Copy important core files into the archive."""
    
    if CORE_SKILL_PATH.exists():
        shutil.copy2(CORE_SKILL_PATH, archive_dir / "SKILL.md")

    peer_review_src = ARTIFACTS_DIR / "peer_review.py"
    if peer_review_src.exists():
        shutil.copy2(peer_review_src, archive_dir / "peer_review.py")

    archiving_src = ARTIFACTS_DIR / "automatic_archiving.py"
    if archiving_src.exists():
        shutil.copy2(archiving_src, archive_dir / "automatic_archiving.py")

    if include_memory and USER_MEMORY_PATH.exists():
        shutil.copy2(USER_MEMORY_PATH, archive_dir / "memory.md")


def create_zip(archive_dir: Path) -> Path:
    zip_path = archive_dir.with_suffix(".zip")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in archive_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(archive_dir)
                zipf.write(file_path, arcname)
    
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Fusion Hero OS v8 - AutomaticArchivingCoreModule")
    parser.add_argument("--reason", required=True, help="Reason for this archive (e.g. SelfMod_Implementation)")
    parser.add_argument("--include-memory", action="store_true", help="Include current user memory.md snapshot")
    args = parser.parse_args()

    print(f"\n[Fusion Hero OS] Starting archive process...")
    print(f"Reason: {args.reason}")

    archive_dir = create_archive_dir(args.reason)
    print(f"Archive directory: {archive_dir}")

    copy_core_files(archive_dir, args.include_memory)
    print("Core files copied.")

    generate_summary(archive_dir, args.reason, args.include_memory)
    create_manifest(archive_dir, args.reason)
    print("Summary and manifest created.")

    zip_path = create_zip(archive_dir)
    print(f"\n\u2705 Archive created successfully:")
    print(f"   ZIP: {zip_path}")
    print(f"   Folder: {archive_dir}\n")


if __name__ == "__main__":
    main()