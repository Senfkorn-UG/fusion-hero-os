import dimod
import neal
from typing import Any
from datetime import datetime

import structlog

from normal_os.core.models import QUBOProblem, QUBOSolution

logger = structlog.get_logger(__name__)


class QUBOSolver:
    """Explicit, production-grade QUBO solver with caching and multiple backends."""

    def __init__(self, solver: str = "auto", cache_enabled: bool = True):
        self.solver = solver
        self.cache_enabled = cache_enabled
        self._neal_sampler = neal.SimulatedAnnealingSampler()
        self._solution_cache: dict[str, QUBOSolution] = {}

    def solve(
        self,
        problem: QUBOProblem,
        num_reads: int = 1000,
        use_cache: bool = True,
    ) -> QUBOSolution:
        problem_id = problem.id or self._generate_problem_id(problem)

        # Check cache
        if use_cache and self.cache_enabled and problem_id in self._solution_cache:
            logger.info("cache_hit", problem_id=problem_id)
            cached = self._solution_cache[problem_id]
            cached.cached = True
            return cached

        # Build full QUBO (merge bias into diagonal)
        Q_full = dict(problem.Q)
        for i, b in problem.bias.items():
            key = (i, i)
            Q_full[key] = Q_full.get(key, 0.0) + b

        bqm = dimod.BinaryQuadraticModel.from_qubo(Q_full)

        # Solve
        if self.solver in ("neal", "auto"):
            response = self._neal_sampler.sample(bqm, num_reads=num_reads)
            best = response.first

            solution = QUBOSolution(
                problem_id=problem_id,
                solution={int(k): int(v) for k, v in best.sample.items()},
                energy=float(best.energy),
                num_reads=num_reads,
                solver="neal",
            )
        else:
            # Placeholder for future GPU / custom solvers
            raise NotImplementedError(f"Solver {self.solver} not implemented yet")

        if self.cache_enabled:
            self._solution_cache[problem_id] = solution

        logger.info(
            "qubo_solved",
            problem_id=problem_id,
            energy=solution.energy,
            solver=solution.solver,
        )
        return solution

    def _generate_problem_id(self, problem: QUBOProblem) -> str:
        import hashlib
        content = str(sorted(problem.Q.items())) + str(sorted(problem.bias.items()))
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def clear_cache(self) -> None:
        self._solution_cache.clear()