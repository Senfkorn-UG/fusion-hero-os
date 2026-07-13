"""
AscensionOS Main Orchestrator

Coordinates all layers:
- Core: LLM Router, QUBO Solver, Agents, Connectors
- Ascension Core: Coevolutionary Closure, Persistent Sisyphos, AscensionCore, Generational Engine
- Heroic Core: Layer 0 MasterSeed, Layer 4 PMS Evidence Spine, Layer 5 QuadCoreBridge
- Kernel AI: Hybrid Cognition, LLM Engine, LLM Merge, Request Optimizer
- Integration Hub: Mesh Connectors, Tailscale Mesh, LLM Frameworks, VR/Assets
- Math/QUBO: Advanced QUBO, Qdrant Cache, QUBO-Llama Bridge
- Self-Modification: Self-Mod Proposals, Critical Meta-Analysis, Anti-Loop Guard
- TTS: Voice Router
- Framework: Skills, Heroic Core Foundation
"""

from typing import Any, Dict, Optional, List
import structlog

from ..llm.router import LLMRouter
from ..optimization.qubo_solver import QUBOSolver
from ..agents.registry import AgentRegistry
from ..connectors.registry import ConnectorRegistry
from ..core.models import Task, OptimizationResult
from ..core.config import AscensionOSConfig

logger = structlog.get_logger()


class AscensionOrchestrator:
    """High-level coordinator for AscensionOS — integrates all layers."""

    def __init__(self, config: Optional[AscensionOSConfig] = None):
        self.config = config or AscensionOSConfig()
        
        # Core normalOS
        self.llm = LLMRouter()
        self.qubo = QUBOSolver()
        self.agents = AgentRegistry()
        self.connectors = ConnectorRegistry()
        self.tasks: List[Task] = []
        
        # AscensionOS Core
        self._coevolutionary_closure = None
        self._persistent_sisyphos = None
        self._ascension_core = None
        self._generational_engine = None
        
        # Heroic Core
        self._master_seed = None
        self._pms_evidence_spine = None
        self._quad_core_bridge = None
        self._heroic_math_engine = None
        
        # Kernel AI
        self._kernel_ai = None
        self._ipc_bridge = None
        
        # Integration Hub
        self._integration_hub = None
        self._mesh_connectors = None
        self._tailscale_mesh = None
        
        # VR/Assets
        self._vr = None
        
        # Math/QUBO
        self._advanced_qubo = None
        self._qubo_qdrant_cache = None
        self._qubo_llama_bridge = None
        
        # Self-Modification
        self._self_mod = None
        
        # TTS
        self._tts = None
        
        # Framework
        self._framework = None

    # --- Core Initialization ---
    
    async def initialize_connectors(self):
        """Connect all enabled external connectors at startup."""
        results = await self.connectors.connect_all()
        logger.info("connectors_initialized", results=results)
        return results

    async def initialize_ascension_core(self):
        """Initialize AscensionOS core modules."""
        if self.config.ascension_core.enabled:
            from ..ascension.ascension_core import AscensionCore
            from ..ascension.coevolutionary_closure import CoevolutionaryClosure
            from ..ascension.persistent_sisyphos import PersistentSisyphos
            from ..ascension.generational_engine import GenerationalEngine
            
            self._ascension_core = AscensionCore(self.config.ascension_core)
            self._coevolutionary_closure = CoevolutionaryClosure(self.config.coevolutionary_closure)
            self._persistent_sisyphos = PersistentSisyphos(self.config.persistent_sisyphos)
            self._generational_engine = GenerationalEngine(self.config.generational_engine)
            
            logger.info("ascension_core_initialized")

    async def initialize_heroic_core(self):
        """Initialize Heroic Core layers (0, 4, 5)."""
        if self.config.heroic_core.enabled:
            from ..ascension.heroic_core_orchestrator import MasterSeed, PMSEvidenceSpine, QuadCoreBridge
            from ..ascension.heroic_math_engine import HeroicMathEngine
            
            self._master_seed = MasterSeed(self.config.master_seed)
            self._pms_evidence_spine = PMSEvidenceSpine(self.config.pms_evidence_spine)
            self._quad_core_bridge = QuadCoreBridge(self._pms_evidence_spine)
            self._heroic_math_engine = HeroicMathEngine(self.config.heroic_math_engine)
            
            # Initialize QuadCoreBridge with spine
            self._quad_core_bridge.spine = self._pms_evidence_spine
            
            logger.info("heroic_core_initialized")

    async def initialize_kernel_ai(self):
        """Initialize Kernel AI components."""
        if self.config.kernel_ai.enabled:
            self._ipc_bridge = None  # Loaded on demand
            logger.info("kernel_ai_initialized")

    async def initialize_integration_hub(self):
        """Initialize Integration Hub (Mesh, LLM, VR, Workstation)."""
        if self.config.integration_hub.enabled:
            from ..integration.fusion_integration_hub import get_full_status, build_graph
            
            self._integration_hub = {
                "get_full_status": get_full_status,
                "build_graph": build_graph,
            }
            
            from ..integration.mesh_connectors import MeshConnectorRegistry
            self._mesh_connectors = MeshConnectorRegistry(self.config.mesh_connectors)
            
            from ..integration.tailscale_mesh_registry import get_mesh_status
            self._tailscale_mesh = {"get_mesh_status": get_mesh_status}
            
            logger.info("integration_hub_initialized")

    async def initialize_vr(self):
        """Initialize VR/Assets."""
        if self.config.vr.enabled:
            logger.info("vr_initialized", assets_root=self.config.vr.assets_root)

    async def initialize_advanced_qubo(self):
        """Initialize Advanced QUBO & Qdrant Cache."""
        if self.config.advanced_qubo.enabled:
            from ..math.advanced_qubo import AdvancedQUBOSolver
            self._advanced_qubo = AdvancedQUBOSolver(self.config.advanced_qubo)
            
        if self.config.qubo_qdrant_cache.enabled:
            from ..math.qubo_qdrant_cache import QUBOQdrantCache
            self._qubo_qdrant_cache = QUBOQdrantCache(self.config.qubo_qdrant_cache)
            
        if self.config.qubo_llama_bridge.enabled:
            logger.info("qubo_llama_bridge_available")
            
        logger.info("advanced_qubo_initialized")

    async def initialize_self_mod(self):
        """Initialize Self-Modification system."""
        if self.config.self_mod.enabled:
            from ..self_mod.self_mod_proposals import SelfModProposalEngine
            self._self_mod = SelfModProposalEngine(self.config.self_mod)
            logger.info("self_mod_initialized")

    async def initialize_tts(self):
        """Initialize TTS Voice Router."""
        if self.config.tts.enabled:
            from ..tts.tts_router import TTSRouter
            self._tts = TTSRouter(self.config.tts)
            logger.info("tts_initialized")

    async def initialize_framework(self):
        """Initialize Framework/Skills."""
        if self.config.framework.enabled:
            logger.info("framework_initialized", skills_dir=self.config.framework.skills_dir)

    async def initialize_all(self):
        """Initialize all AscensionOS subsystems."""
        await self.initialize_connectors()
        await self.initialize_ascension_core()
        await self.initialize_heroic_core()
        await self.initialize_kernel_ai()
        await self.initialize_integration_hub()
        await self.initialize_vr()
        await self.initialize_advanced_qubo()
        await self.initialize_self_mod()
        await self.initialize_tts()
        await self.initialize_framework()
        logger.info("ascensionos_fully_initialized")

    # --- Core Task Management ---
    
    async def add_task(self, description: str, priority: int = 5, **kwargs) -> Task:
        task = Task(description=description, priority=priority, **kwargs)
        self.tasks.append(task)
        logger.info("task_added", task_id=task.id, description=description)
        return task

    def optimize_schedule(self) -> OptimizationResult:
        if not self.tasks:
            return OptimizationResult(task_order=[], energy=0.0, solver_time_ms=0.0)
        result = self.qubo.optimize_task_order(self.tasks)
        logger.info("schedule_optimized", num_tasks=len(self.tasks), energy=result.energy)
        return result

    async def run_task_with_llm(self, task: Task, prompt: str) -> Dict[str, Any]:
        task.status = "running"
        try:
            response = await self.llm.generate(prompt)
            task.status = "completed"
            return {
                "task_id": task.id,
                "status": "completed",
                "llm_response": response.content,
                "provider": response.provider,
            }
        except Exception as e:
            task.status = "failed"
            logger.error("task_failed", task_id=task.id, error=str(e))
            raise

    # --- Connector Access ---
    
    async def use_connector(self, connector_name: str, action: str, params: Dict) -> Dict:
        """Execute an action on any registered connector."""
        connector = self.connectors.get(connector_name)
        if not connector:
            raise ValueError(f"Connector '{connector_name}' not found")
        result = await connector.execute(action, params)
        return result.model_dump()

    # --- Ascension Core Methods ---
    
    async def run_coevolutionary_closure(self, task_data: Dict) -> Dict:
        """Execute Co-Evolutionary Closure cycle."""
        if not self._coevolutionary_closure:
            raise RuntimeError("Ascension core not initialized")
        return await self._coevolutionary_closure.run_cycle(task_data)

    async def run_persistent_sisyphos(self, problem: Dict) -> Dict:
        """Execute Persistent Sisyphos improvement loop."""
        if not self._persistent_sisyphos:
            raise RuntimeError("Persistent Sisyphos not initialized")
        return await self._persistent_sisyphos.improve(problem)

    async def run_generational_engine(self, config: Dict) -> Dict:
        """Run Generational Evolution Engine."""
        if not self._generational_engine:
            raise RuntimeError("Generational Engine not initialized")
        return await self._generational_engine.evolve(config)

    # --- Heroic Core Methods ---
    
    def verify_master_seed_integrity(self, current_state_hash: str) -> bool:
        """Verify Master Seed integrity (Layer 0)."""
        if not self._master_seed:
            raise RuntimeError("Heroic Core not initialized")
        return self._master_seed.verify_integrity(current_state_hash)

    def execute_pms_operator_chain(self, operator_id: str, payload: Dict) -> Dict:
        """Execute PMS Operator Chain (Layer 4)."""
        if not self._pms_evidence_spine:
            raise RuntimeError("PMS Evidence Spine not initialized")
        return self._pms_evidence_spine.execute_operator_chain(operator_id, payload)

    def quad_core_route(self, domain: str, payload: Dict) -> Dict:
        """Route through QuadCore Bridge (Layer 5)."""
        if not self._quad_core_bridge:
            raise RuntimeError("QuadCore Bridge not initialized")
        return self._quad_core_bridge.route(domain, payload)

    # --- Integration Hub Methods ---
    
    async def get_full_system_status(self) -> Dict:
        """Get complete system status graph."""
        if not self._integration_hub:
            raise RuntimeError("Integration Hub not initialized")
        return await self._integration_hub["get_full_status"]()

    async def build_system_graph(self) -> Dict:
        """Build linked system graph."""
        if not self._integration_hub:
            raise RuntimeError("Integration Hub not initialized")
        return await self._integration_hub["build_graph"]()

    async def get_mesh_status(self) -> Dict:
        """Get Tailscale mesh status."""
        if not self._tailscale_mesh:
            raise RuntimeError("Tailscale mesh not initialized")
        return await self._tailscale_mesh["get_mesh_status"]()

    # --- Advanced QUBO Methods ---
    
    def solve_qubo_advanced(self, problem: Dict, strategy: str = "auto") -> Dict:
        """Solve QUBO with advanced strategies."""
        if not self._advanced_qubo:
            raise RuntimeError("Advanced QUBO not initialized")
        return self._advanced_qubo.solve(problem, strategy)

    def get_qubo_cached_solution(self, problem_hash: str) -> Optional[Dict]:
        """Retrieve cached QUBO solution."""
        if not self._qubo_qdrant_cache:
            return None
        return self._qubo_qdrant_cache.get(problem_hash)

    def cache_qubo_solution(self, problem_hash: str, solution: Dict):
        """Cache QUBO solution."""
        if self._qubo_qdrant_cache:
            self._qubo_qdrant_cache.set(problem_hash, solution)

    # --- Self-Modification Methods ---
    
    def propose_self_modification(self, proposal: Dict) -> Dict:
        """Submit self-modification proposal."""
        if not self._self_mod:
            raise RuntimeError("Self-modification not initialized")
        return self._self_mod.propose(proposal)

    def analyze_critical_meta(self, context: Dict) -> Dict:
        """Run critical meta-analysis."""
        if not self._self_mod:
            raise RuntimeError("Self-modification not initialized")
        return self._self_mod.critical_meta_analysis(context)

    # --- TTS Methods ---
    
    async def synthesize_speech(self, text: str, voice: str = None) -> bytes:
        """Synthesize speech via TTS Router."""
        if not self._tts:
            raise RuntimeError("TTS not initialized")
        return await self._tts.synthesize(text, voice)

    # --- Lifecycle ---
    
    async def close(self):
        await self.llm.close()
        if self._ipc_bridge:
            await self._ipc_bridge.close()
        logger.info("ascensionos_shutdown_complete")
