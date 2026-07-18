"""Tests für das Hyperclusterup Zitterpolymesh (PVHT-Scheduler)."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from fusion_hero_os.core.zitterpolymesh import (
    LaneKind,
    LaneProfile,
    MeshValidationError,
    ZitterJitter,
    ZitterPolyMesh,
    builtin_ops,
    detect_lanes,
    load_pipeline,
    mesh_from_pipeline,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_FILE = REPO_ROOT / "zitterpolymesh_pipeline.yaml"


def small_lanes() -> dict:
    return {
        kind: LaneProfile(kind=kind, workers=2, backend="threadpool", virtual=kind != LaneKind.CPU)
        for kind in LaneKind
    }


def test_detect_lanes_has_all_four_and_qpu_is_honest():
    lanes = detect_lanes()
    assert set(lanes) == set(LaneKind)
    assert lanes[LaneKind.QPU].virtual is True  # nie ein echter QPU
    assert lanes[LaneKind.CPU].workers >= 2


def test_zitter_jitter_is_damped_and_bounded():
    j = ZitterJitter(base=0.01, ceiling=0.5)
    delays = [j.delay(a) for a in range(10)]
    assert all(0.0 <= d <= 0.5 for d in delays)
    # späte Versuche sitzen am Ceiling-Fixpunkt
    assert delays[-1] == pytest.approx(0.5)


def test_validate_rejects_unknown_dep_and_cycle():
    mesh = ZitterPolyMesh(lanes=small_lanes())
    mesh.add_task("a", "cpu", lambda ctx: 1, deps=["ghost"])
    with pytest.raises(MeshValidationError, match="unbekannte Dependency"):
        mesh.validate()

    mesh2 = ZitterPolyMesh(lanes=small_lanes())
    mesh2.add_task("a", "cpu", lambda ctx: 1, deps=["b"])
    mesh2.add_task("b", "cpu", lambda ctx: 1, deps=["a"])
    with pytest.raises(MeshValidationError, match="Zyklus"):
        mesh2.validate()


def test_dependencies_are_respected_and_results_flow():
    events: list[str] = []
    lock = threading.Lock()

    def rec(name):
        def fn(ctx):
            with lock:
                events.append(name)
            return name

        return fn

    mesh = ZitterPolyMesh(lanes=small_lanes())
    mesh.add_task("root", "cpu", rec("root"))
    mesh.add_task("mid", "mem", rec("mid"), deps=["root"])
    mesh.add_task("leaf", "qpu", lambda ctx: ctx["deps"], deps=["mid"])
    report = mesh.run(timeout=30.0)

    assert report["ok"] is True
    assert events.index("root") < events.index("mid")
    # Ergebnis der Dependency wird in den Kontext gereicht
    assert report["tasks"]["leaf"]["result"] == {"mid": "mid"}


def test_independent_lanes_run_in_parallel():
    barrier = threading.Barrier(3, timeout=5.0)

    def sync_task(ctx):
        barrier.wait()  # hängt, bis alle 3 gleichzeitig laufen
        return True

    mesh = ZitterPolyMesh(lanes=small_lanes())
    mesh.add_task("p-cpu", "cpu", sync_task)
    mesh.add_task("p-mem", "mem", sync_task)
    mesh.add_task("p-gpu", "gpu", sync_task)
    report = mesh.run(timeout=30.0)
    # Barrier(3) kann nur fallen, wenn die Lanes wirklich parallel liefen
    assert report["ok"] is True


def test_retry_with_jitter_then_success():
    attempts = {"n": 0}

    def flaky(ctx):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("zitter")
        return "stable"

    mesh = ZitterPolyMesh(
        lanes=small_lanes(),
        jitter=ZitterJitter(base=0.001, ceiling=0.01),
    )
    mesh.add_task("flaky", "cpu", flaky, retries=4)
    report = mesh.run(timeout=30.0)
    assert report["ok"] is True
    assert report["tasks"]["flaky"]["attempts"] == 3


def test_failed_task_skips_dependents():
    def boom(ctx):
        raise RuntimeError("kaputt")

    mesh = ZitterPolyMesh(
        lanes=small_lanes(),
        jitter=ZitterJitter(base=0.001, ceiling=0.01),
    )
    mesh.add_task("boom", "cpu", boom, retries=1)
    mesh.add_task("after", "mem", lambda ctx: 1, deps=["boom"])
    mesh.add_task("free", "cpu", lambda ctx: 1)
    report = mesh.run(timeout=30.0)

    assert report["ok"] is False
    assert report["tasks"]["boom"]["status"] == "failed"
    assert report["tasks"]["after"]["status"] == "skipped"
    assert report["tasks"]["free"]["status"] == "ok"


def test_builtin_ops_do_real_verified_work():
    ops = builtin_ops()
    lane_ctx = {"payload": {}, "deps": {}, "lane": {"backend": "cpu-fallback"}}
    assert ops["cpu_sum_squares"]({**lane_ctx, "payload": {"n": 1000}})["sum_squares"] > 0
    assert ops["mem_shard_roundtrip"]({**lane_ctx, "payload": {"bytes": 10_000}})["sha256"]
    assert ops["gpu_matmul"]({**lane_ctx, "payload": {"n": 8}})["checksum"] == 512.0
    qpu = ops["qpu_min_qubo"](lane_ctx)
    assert qpu["energy"] == pytest.approx(-3.0)
    assert qpu["virtual"] is True


def test_pipeline_file_loads_and_all_workflows_validate():
    pipeline = load_pipeline(PIPELINE_FILE)
    assert pipeline["mesh"] == "hyperclusterup-zitterpolymesh"
    for wf in pipeline["workflows"]:
        order = mesh_from_pipeline(pipeline, wf, lanes=small_lanes()).validate()
        assert order, f"Workflow {wf} ohne Tasks"


def test_boot_fluid_workflow_runs_end_to_end():
    pipeline = load_pipeline(PIPELINE_FILE)
    mesh = mesh_from_pipeline(pipeline, "boot-fluid", lanes=small_lanes())
    report = mesh.run(timeout=120.0)
    assert report["ok"] is True
    assert report["tasks"]["merge-lanes"]["status"] == "ok"
    # Alle vier Lanes wurden benutzt
    used = {r["lane"] for r in report["tasks"].values()}
    assert used == {"cpu", "mem", "gpu", "qpu"}
