# -*- coding: utf-8 -*-
from fusion_hero_os.core.dns_tor_stack import (
    load_config,
    _build_query,
    _parse_qname,
    resolve_once,
    status,
)


def test_config_ports():
    cfg = load_config()
    assert cfg.get("version") == "1.0"
    tor = cfg.get("tor") or {}
    proxy = cfg.get("local_proxy") or {}
    assert int(tor.get("dns_port")) == 8853
    assert int(proxy.get("listen_port")) == 5454
    assert "9.9.9.9" in (cfg.get("clearnet_upstream") or [])


def test_build_and_parse_query():
    q = _build_query("example.com")
    assert len(q) >= 12
    name, _ = _parse_qname(q, 12)
    assert name == "example.com"


def test_resolve_clearnet():
    r = resolve_once("example.com")
    assert r.get("ok") is True
    assert r.get("via") == "clearnet"
    assert r.get("bytes", 0) >= 30


def test_status_shape():
    st = status()
    assert st.get("ok")
    assert "5454" in st.get("proxy_listen", "")
