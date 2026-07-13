# ⚔️ Fusion Hero Core

**ALTE_Frau_95g Heroic Core - Clean Implementation v7.5+**

Clean, production-oriented version of the Fusion Hero OS.

## Features

- Unified Launcher (`start_fusion_hero.py`)
- C ↔ Python IPC Bridge (AF_UNIX + length-prefixed protocol)
- Full integration of historical beta versions from archive
- Designed for Hyperthreading and future Rust kernel

## Quick Start

```bash
python start_fusion_hero.py
python start_fusion_hero.py --with-dashboard
python start_fusion_hero.py --list-versions
```

## Repository Structure

```
fusion-hero-core/
├── start_fusion_hero.py          # Main launcher
├── kernel/bridge/                # C + Python IPC Bridge
└── 06_Master_Archive/            # All previous beta/experimental versions
```

**This is the clean reference core.** All previous versions remain preserved.
