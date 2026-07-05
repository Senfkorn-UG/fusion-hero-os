#!/usr/bin/env python3
"""
Fusion Hero OS - Minimal Viable C-Kernel ↔ Python Bridge
Python Client (ICD v1.0 compliant)
"""

import socket
import struct
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("FusionHeroIPC")

class IPCProtocolError(Exception):
    pass

class IPCConnectionError(Exception):
    pass

class FusionHeroIPCClient:
    MAGIC = 0x46484F53
    VERSION = 0x01
    HEADER_FORMAT = ">IBBHII"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, socket_path: str = "/tmp/fusion_hero_ipc.sock"):
        self.socket_path = socket_path
        self.sock: Optional[socket.socket] = None

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.socket_path)
            logger.info(f"Connected to kernel at {self.socket_path}")
        except socket.error as e:
            self.sock = None
            raise IPCConnectionError(f"Failed to connect to {self.socket_path}") from e

    def disconnect(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def _recv_exact(self, num_bytes: int) -> bytes:
        buffer = bytearray()
        while len(buffer) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(buffer))
            if not chunk:
                raise IPCConnectionError("Connection closed by kernel")
            buffer.extend(chunk)
        return bytes(buffer)

    def send_request(self, msg_type: int, payload: bytes = b"") -> Dict[str, Any]:
        if not self.sock:
            raise IPCConnectionError("Not connected")

        payload_len = len(payload)
        header = struct.pack(self.HEADER_FORMAT, self.MAGIC, self.VERSION, msg_type, 0x0000, payload_len, 0x00000000)
        self.sock.sendall(header + payload)

        raw_header = self._recv_exact(self.HEADER_SIZE)
        magic, version, msg_type, status_code, payload_len, reserved = struct.unpack(self.HEADER_FORMAT, raw_header)

        if magic != self.MAGIC:
            raise IPCProtocolError(f"Invalid magic: 0x{magic:08X}")
        if version != self.VERSION:
            raise IPCProtocolError(f"Version mismatch")

        payload = b""
        if payload_len > 0:
            payload = self._recv_exact(payload_len)

        return {
            "msg_type": msg_type,
            "status_code": status_code,
            "payload_len": payload_len,
            "payload": payload
        }

if __name__ == "__main__":
    print("Fusion Hero IPC Client - Ready")