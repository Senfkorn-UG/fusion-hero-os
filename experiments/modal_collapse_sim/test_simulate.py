"""
Fusion Hero OS - Modal Kollaps Tests (Layer 0 Verifikation)
"""

import pytest
from experiments.modal_collapse_sim.simulate import (
    Entity,
    ModalCollapseDynamik,
    SimulationResult
)

def test_simulation_converges():
    """Testet den glücklichen Pfad: Ausreichend Energie für den Kollaps."""
    sim = ModalCollapseDynamik(k_spring=2.0, r_critical=3.0)
    result = sim.run_simulation(Entity("Ego", 10.0), Entity("Heroic Core", 100.0))

    assert result.converged is True
    assert result.iterations > 0
    assert result.final_delta <= 0.01
    assert result.final_efficiency > 0.1
    assert result.remaining_energy >= 0.0

def test_simulation_stagnates_due_to_low_energy():
    """Testet das Scheitern: Zu wenig Spannung (k=0.2) führt zur Stagnation."""
    sim = ModalCollapseDynamik(k_spring=0.2, r_critical=3.0)
    result = sim.run_simulation(Entity("Ego", 10.0), Entity("Heroic Core", 100.0))

    assert result.converged is False
    assert result.remaining_energy <= 0.0
    assert result.final_delta > 0.01 # Differenz konnte nicht aufgelöst werden

@pytest.mark.parametrize("k_spring, expected_convergence", [
    (3.0, True),   # Massive Spannung -> Garantiert Konvergenz
    (1.5, True),   # Moderate Spannung -> Reicht knapp
    (0.5, False),  # Niedrige Spannung -> Stagnation (Energie geht vorzeitig aus)
])
def test_energy_boundaries(k_spring, expected_convergence):
    """Parametrisierter Grenztest für das ontologische Budget."""
    sim = ModalCollapseDynamik(k_spring=k_spring, r_critical=3.0)
    result = sim.run_simulation(Entity("Ego", 10.0), Entity("Heroic Core", 100.0))
    
    assert result.converged == expected_convergence