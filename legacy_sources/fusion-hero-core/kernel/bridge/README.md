# C ↔ Python IPC Bridge

Minimal Viable Bridge between C Kernel and Python Userland using AF_UNIX sockets.

## Files

- `fhos_ipc_server.c` - C server (single-threaded MVP)
- `fhos_ipc_client.py` - Python client

## Protocol

- 16-byte length-prefixed header
- Magic: `0x46484F53` ("FHOS")
- Big-Endian
- Strict struct packing

## Usage

See root `start_fusion_hero.py` for integration.
