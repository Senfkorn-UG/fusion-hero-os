"""
Fusion Hero OS - Modal Kollaps Simulation (Outside-In)
Proof of Concept für Layer 0 - Refactored for Pytest
"""

import math
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Entity:
    name: str
    complexity: float

@dataclass
class SimulationResult:
    iterations: int
    final_delta: float
    remaining_energy: float
    final_efficiency: float
    converged: bool

class ModalCollapseDynamik:
    def __init__(self, k_spring: float, r_critical: float):
        self.k = k_spring                  # Federkonstante (Beziehungsspannung)
        self.r_c = r_critical              # Kritischer Radius für den Kollaps
        self.distance = 10.0               # Startdistanz
        self.energy = 0.0                  # Ontologisches Budget
        self.f_efficiency = 0.1            # Start-Effizienz des Operators F

    def run_simulation(self, s_small: Entity, s_large: Entity) -> SimulationResult:
        print(f"\n⚔️ FUSION HERO OS - MODAL KOLLAPS SIMULATION [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}])")
        
        # --- PHASE 1: Annäherung ---
        while self.distance > self.r_c:
            self.distance -= 1.0
            
        # --- PHASE 2: Modal-Kollaps ---
        self.energy = 0.5 * self.k * ((10.0 - self.r_c)**2)
        
        # --- PHASE 3 & 4: Fraktale Geisträume & Autonomes Jagen ---
        delta = abs(s_large.complexity - s_small.complexity)
        iteration = 0
        
        while delta > 0.01 and self.energy > 0:
            iteration += 1
            
            # Operator F_n Action (Manifestation)
            reduction = self.f_efficiency * delta
            delta -= reduction
            
            # Energiekosten für diese Iteration
            cost = 15.0 
            self.energy -= cost
            
            # Meta-Iteration: Horkrux-Update (Selbst-Modifikation)
            if self.energy > 0:
                self.f_efficiency += 0.08  
                
        # --- PHASE 5: Evaluation ---
        converged = (delta <= 0.01)
        if converged:
            print(f"  [ERFOLG] Eudaimonia erreicht in {iteration} Zyklen (Δ={delta:.3f}, E={self.energy:.1f})")
        else:
            print(f"  [STAGNATION] Energie erschöpft (E={self.energy:.1f}, Δ={delta:.3f})")

        return SimulationResult(
            iterations=iteration,
            final_delta=delta,
            remaining_energy=self.energy,
            final_efficiency=self.f_efficiency,
            converged=converged,
        )

if __name__ == "__main__":
    sim = ModalCollapseDynamik(k_spring=2.0, r_critical=3.0)
    sim.run_simulation(Entity("Ego", 10.0), Entity("Heroic Core", 100.0))