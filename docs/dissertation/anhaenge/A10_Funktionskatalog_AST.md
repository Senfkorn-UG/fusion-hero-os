# A10 — Funktionskatalog (maschinell aus AST)

**Geltung:** Spezifikation (Inventar des Codes, Stand Generator-Lauf).
**Nicht:** Beweis der Korrektheit einzelner Funktionen.
**Designvorlage:** V3.3 — Katalog = Spezifikation; Herleitungen in A01–A09.

**Dateien:** 78 · **Klassen:** 181 · **Top-Level-Funktionen:** 181

Regenerieren: `python scripts/generate_anhang_katalog.py`

## `fusion_hero_os/bridge/gateway.py`

### class `IPCGateway`
- public: `status`, `dispatch`, `math_status`, `orchestrator_status`
- intern: `__init__`, `_connect`
- def `get_ipc_gateway`

## `fusion_hero_os/bridge/router.py`

- def `_json_safe`
- def `route_dispatch`
- def `_v8_import`
- def `route_list_modules`
- def `handle_ipc_message`

## `fusion_hero_os/config.py`

- def `_env_int`
- def `_env_set`
### class `DispatcherConfig`
- (Datenklasse / ohne Methoden)
- def `_max_workers_or_none`
- def `get_config`

## `fusion_hero_os/core/base_module.py`

### class `EvolutionProposal`
- (Datenklasse / ohne Methoden)
### class `ReviewCriterion`
- (Datenklasse / ohne Methoden)
### class `ReviewResult`
- public: `passed`, `score`, `report`
### class `BaseModule`
- public: `process`, `propose_evolution`, `peer_review`
- intern: `__init__`

## `fusion_hero_os/core/cec.py`

### class `CoEvolutionaryClosure`
- public: `step`
- intern: `__init__`, `_calculate_coherence`

## `fusion_hero_os/core/dashboard/orchestration.py`

### class `DashboardOrchestrator`
- public: `register_agent`, `assign_best_agent`, `get_active_agents`
- intern: `__init__`

## `fusion_hero_os/core/dashboard/workspace.py`

### class `Workspace`
- public: `set`, `get`, `clear`
- intern: `__init__`

## `fusion_hero_os/core/dependency_atlas.py`

### class `Node`
- (Datenklasse / ohne Methoden)
### class `Edge`
- (Datenklasse / ohne Methoden)
### class `Atlas`
- public: `to_dict`, `epistemik_summary`
- def `_layer_prefixes_from_unified`
- def `assign_layer`
- def `_iter_python_files`
- def `_module_name`
- def `_top_level_imports`
- def `_resolve_absolute`
- def `_resolve_relative`
- def `scan_python`
- def `_parse_cargo_dependencies`
- def `scan_rust`
- def `scan_js`
- def `find_cycles`
- def `build_atlas`
- def `_repo_state_signature`
- def `_layer_prefixes_cached`
- def `build_atlas_cached`
- def `_package_key`
- def `render_mermaid`
- def `render_markdown`
- def `main`

## `fusion_hero_os/core/dispatcher.py`

### class `ModuleNotRegisteredError`
- (Datenklasse / ohne Methoden)
### class `Dispatcher`
- public: `register`, `unregister`, `list_modules`, `dispatch`, `dispatch_many`, `propose_evolution`, `collect_evolution_proposals`, `peer_review`
- intern: `__init__`, `_get`
- def `build_default_dispatcher`
- def `get_default_dispatcher`

## `fusion_hero_os/core/grok_interconnect.py`

### class `GrokNode`
- (Datenklasse / ohne Methoden)
### class `GrokEdge`
- (Datenklasse / ohne Methoden)
### class `InterconnectGraph`
- public: `to_dict`
- def `probe_http`
- def `_tcp_open`
- def `_read_json`
- def `capture`
- def `evolve`
- def `get_graph`
- def `_persist`
- def `_read_json`

## `fusion_hero_os/core/grok_route_table.py`

### class `RouteTarget`
- public: `to_dict`
- def `resolve`
- def `route_message`
- def `all_routes`

## `fusion_hero_os/core/heroic_core.py`

### class `HeroicCore`
- public: `register_module`, `get_llm`, `get_sisyphos_state`, `enforce_fail_closed`, `trigger_psycholysis_if_needed`, `status`
- intern: `__init__`, `_dummy_context`
- def `get_heroic_core`

## `fusion_hero_os/core/heroic_core_orchestrator.py`

### class `MasterSeed`
- public: `state_hash`, `verify_integrity`
### class `PMSEvidenceSpine`
- public: `available`, `execute_operator_chain`, `validate_chain`
- intern: `__init__`, `_run`
### class `QuadCoreBridge`
- public: `invoke_phoenix_mode`, `process_query`, `ask_llm`, `run_ascension_generation`
- intern: `__init__`, `_flush_volatile_memory`
- def `bootstrap_v8_system`

## `fusion_hero_os/core/heroic_math_engine.py`

### class `HeroicMatrixEngine`
- public: `compute_commutator`, `check_reciprocity_condition`, `check_transpose_reciprocity`
- intern: `__init__`
### class `OrthogonalProjector`
- public: `project`, `is_idempotent`, `is_symmetric`, `spectrum_in_01`, `is_nonexpansive_for`
- intern: `__init__`
### class `StableCoreLattice`
- public: `is_less_or_equal`, `get_join`
- intern: `__init__`, `_apply_transitive_closure`
### class `RepairedStructureIP`
- public: `compute_stability`, `check_compatibility`, `check_monotone_domain`, `fusion_operator`
- intern: `__init__`
### class `BanachContractionSeed`
- public: `apply`, `fixpoint`, `iterate`, `verify_contraction_bound`
- intern: `__init__`
- def `run_sandbox_verification`

## `fusion_hero_os/core/inference_scheduler_qubo.py`

### class `ScheduleProblem`
- public: `n`, `total_cost`
- intern: `__post_init__`
- def `build_qubo`
- def `greedy_schedule`
- def `solve_schedule`
- def `random_problem`

## `fusion_hero_os/core/layer_registry.py`

- def `_load_yaml`
- def `_load_json`
### class `LayerStatus`
- public: `to_dict`
- def `_paths_from_config`
- def `_check_mesh_layer`
- def `_check_intelligence_layer`
- def `_check_vr_layer`
- def `_check_kernel_layer`
- def `_check_ascension_layer`
- def `_check_knowledge_layer`
- def `erkenntnisse_summary`
- def `get_layer_status`
- def `_build_status`
- def `get_all_layer_status`

## `fusion_hero_os/core/masterseed_sync.py`

### class `SyncState`
- public: `state_hash`
- def `mutual_sync`
- def `sync_evolutions`
- def `identity_preservation_score`

## `fusion_hero_os/core/models.py`

### class `Task`
- (Datenklasse / ohne Methoden)
### class `TaskResult`
- (Datenklasse / ohne Methoden)

## `fusion_hero_os/core/multimodal_protocol.py`

### class `InventoryEntry`
- (Datenklasse / ohne Methoden)
- def `_sha256`
- def `_extract_text`
- def `_extract_pdf`
- def `_extract_image`
- def `classify`
- def `_iter_archive_files`
- def `build_inventory`
- def `_archive_signature`
- def `build_inventory_cached`
- def `_load_frameworks`
- def `provider_access_status`
- def `routing_matrix`
- def `summary`
- def `to_dict`
- def `main`

## `fusion_hero_os/core/psycholysis_trigger.py`

### class `PsycholysisTrigger`
- public: `should_trigger`, `trigger`, `log_somatic_practice`, `complete_session`
- intern: `__init__`

## `fusion_hero_os/core/quantum_cognition.py`

- def `_as_state`
- def `_check_projector`
- def `projector_from_vectors`
### class `BeliefState`
- public: `prob`, `collapse`, `prob_sequence`
- intern: `__init__`
- def `order_effect`
- def `qq_equality_residual`
- def `interference_term`
### class `TwoLevelOscillator`
- public: `unitary`, `unitary_via_spectral`, `transition_probability`, `evolve`
- intern: `__init__`

## `fusion_hero_os/core/quantum_dictionaries.py`

- def `canonical_key`
### class `_Entry`
- (Datenklasse / ohne Methoden)
### class `QuantumDictionary`
- public: `get_or_compute`, `invalidate`, `stats`
- intern: `__init__`
- def `get_quantum_dictionary`
- def `registry_stats`

## `fusion_hero_os/core/race_guard.py`

- def `_as_path`
### class `FileLock`
- public: `acquire`, `release`
- intern: `__init__`, `__enter__`, `__exit__`
- def `file_lock`
- def `atomic_write_text`
- def `atomic_write_json`
- def `locked_atomic_write_json`
- def `_read_json`
- def `compare_and_swap_json`
### class `RaceConditionGuard`
- public: `write_json`, `write_text`, `cas`
- def `race_stress_test`

## `fusion_hero_os/core/rhe.py`

### class `EmbodimentState`
- (Datenklasse / ohne Methoden)
### class `RustHybridEmbodiment`
- public: `update_from_body`, `update_from_theory`, `get_state`
- intern: `__init__`, `_recalculate_coherence`

## `fusion_hero_os/core/universal_llm_router.py`

### class `SisyphosCycle`
- public: `step`, `get_state`
### class `FailClosed`
- public: `enforce`
### class `UnifiedHeroicLLMCore`
- public: `get_best_assignment`, `ask`, `aask`, `initiate_recovery`, `status`
- intern: `__init__`, `_build_heroic_context`, `_classify`, `_score`
- def `get_unified_llm_core`

## `fusion_hero_os/engine/mainframe.py`

- def `_get_pool`
- def `_load_rust_backend`
- def `get_rust_backend`
### class `QUBOProblem`
- intern: `__init__`
### class `SolverResult`
- intern: `__init__`
### class `QUBOSolverConfig`
- intern: `__init__`
- def `_simulated_annealing_kernel`
- def `simulated_annealing`
- def `local_search`
- def `make_Q`
- def `_sa_kernel_trace`
- def `_anneal_one`
- def `parallel_anneal`
- def `warmup_kernels`
### class `SolverBackend`
- public: `solve`
### class `ClassicalBackend`
- public: `solve`
- intern: `__init__`
### class `SelfModifyCoreModule`
- public: `register_audit_hook`
- intern: `__init__`
### class `GenerationalEvolutionProtocolCoreModule`
- public: `run_generation`, `evolve`
- intern: `__init__`, `_clip`, `_random_genome`, `_mutate`, `_target`, `_fitness`, `_init_population`
### class `CriticalMetaAnalysisCoreModule`
- public: `analyze`
### class `ExecutableAuditAgent`
- intern: `__init__`
### class `QUBOIntegrationCoreModule`
- public: `get_ascension_state`, `run_ascension_generation`, `execute_secure_run`, `execute_parallel_run`
- intern: `__init__`, `_interlock_core_hooks`

## `fusion_hero_os/engine/mining_qubo.py`

### class `ExcavatorConnector`
- public: `info`, `speeds`, `workers`
- intern: `_call`
- def `estimate_profit_matrix`
- def `build_profit_switching_qubo`
- def `decode_assignment`
- def `assignment_profit`
- def `optimize_switching`
- def `_mock_rig`
- def `_demo`

## `fusion_hero_os/engine/rust_backend.py`

- def `parallel_anneal_rust`

## `fusion_hero_os/integrations/phone_link/reader.py`

### class `PhoneLinkSnapshot`
- public: `to_dict`
- def `_package_root`
- def `_discover_database`
- def `_filetime_to_iso`
- def `_mask_address`
- def `_is_host_running`
### class `PhoneLinkReader`
- public: `database_path`, `recent_conversations`, `recent_messages`, `counts`, `snapshot`
- intern: `__init__`, `_query`
- def `phone_link_status`

## `fusion_hero_os/mcp/fhero_mcp_server.py`

- def `_tool_layer0_verify`
- def `_tool_schedule_qubo`
- def `_result`
- def `_error`
- def `handle_message`
- def `main`

## `fusion_hero_os/meta/api.py`

- def `get_service`
- def `grant_consent`
- def `ingest`
- def `activate`
- def `associate`
- def `optimize`
- def `audit_trail`
- def `create_app`

## `fusion_hero_os/meta/cli.py`

- def `run_demo`
- def `main`

## `fusion_hero_os/meta/consent.py`

- def `_utcnow`
### class `Purpose`
- (Datenklasse / ohne Methoden)
### class `ConsentError`
- (Datenklasse / ohne Methoden)
### class `ConsentGrant`
- public: `is_active`, `expires_at`, `to_public_dict`
### class `AuditEvent`
- public: `to_dict`
- def `_hash_event`
### class `AuditLog`
- public: `append`, `verify`, `events`, `events_for`
- intern: `__init__`, `__len__`
### class `ConsentStore`
- public: `grant`, `revoke`, `find_active`, `authorize`
- intern: `__init__`

## `fusion_hero_os/meta/coupling.py`

- def `jacobian_fd`
- def `spectral_radius`
- def `operator_norm`
### class `ContractionResult`
- public: `to_dict`
- def `is_contraction`
### class `FixedPointResult`
- public: `to_dict`
- def `iterate_to_fixed_point`

## `fusion_hero_os/meta/fixtures/__init__.py`

- def `load_neutral_fixture`

## `fusion_hero_os/meta/graph.py`

### class `GraphError`
- (Datenklasse / ohne Methoden)
- def `_utcnow_iso`
- def `_canonical_number`
### class `Provenance`
- public: `to_dict`, `now`
### class `GraphSchema`
- public: `to_dict`
### class `Node`
- public: `to_dict`
### class `Edge`
- public: `to_dict`
### class `PropertyGraph`
- public: `add_node`, `add_edge`, `nodes`, `edges`, `snapshot`
- intern: `__init__`
### class `GraphSnapshot`
- public: `schema`, `nodes`, `edges`, `content_hash`, `snapshot_id`, `build`, `to_canonical_json_static`, `to_canonical_json`, `to_dict`, `node_matrix`, `adjacency`
- intern: `__init__`, `_validate`, `_canonical_payload`, `_hash`

## `fusion_hero_os/meta/hebbian.py`

### class `HebbianError`
- (Datenklasse / ohne Methoden)
- def `_key`
### class `HebbianConfig`
- intern: `__post_init__`
### class `HebbianAssociationMemory`
- public: `update`, `update_many`, `decay_all`, `weight`, `delete`, `delete_slot`, `items`, `to_matrix`
- intern: `__init__`, `_clip`, `__len__`

## `fusion_hero_os/meta/pipeline.py`

### class `MetaNeuralService`
- public: `grant_consent`, `revoke_consent`, `sweep_expired`, `ingest`, `snapshot_for`, `activate`, `associate`, `analyze_convergence`, `optimize`, `audit_trail`
- intern: `__init__`, `_require`, `_purge_subject_state`, `_purge_if_expired`

## `fusion_hero_os/meta/qubo_bridge.py`

### class `QUBOBridgeError`
- (Datenklasse / ohne Methoden)
### class `QUBOProblem`
- public: `size`
### class `QUBOResult`
- public: `to_dict`
- def `build_qubo`
- def `energy`
- def `_anneal_numpy`
- def `_brute_force`
- def `solve_qubo`
- def `_try_qb_qubo`

## `fusion_hero_os/meta/schemas.py`

### class `ConsentGrantRequest`
- (Datenklasse / ohne Methoden)
### class `ConsentGrantResponse`
- (Datenklasse / ohne Methoden)
### class `NodeFixture`
- (Datenklasse / ohne Methoden)
### class `EdgeFixture`
- (Datenklasse / ohne Methoden)
### class `IngestRequest`
- (Datenklasse / ohne Methoden)
### class `SnapshotResponse`
- (Datenklasse / ohne Methoden)
### class `ActivateRequest`
- (Datenklasse / ohne Methoden)
### class `ActivationReportResponse`
- (Datenklasse / ohne Methoden)
### class `AssociateRequest`
- (Datenklasse / ohne Methoden)
### class `ConvergenceResponse`
- (Datenklasse / ohne Methoden)
### class `OptimizeRequest`
- (Datenklasse / ohne Methoden)
### class `OptimizeResponse`
- (Datenklasse / ohne Methoden)
### class `AuditEventResponse`
- (Datenklasse / ohne Methoden)
### class `AuditTrailResponse`
- (Datenklasse / ohne Methoden)

## `fusion_hero_os/meta/vault.py`

### class `VaultError`
- (Datenklasse / ohne Methoden)
### class `VaultUnavailableError`
- (Datenklasse / ohne Methoden)
### class `VaultAuthorizationError`
- (Datenklasse / ohne Methoden)
### class `SubjectRef`
- public: `derive`
### class `VaultResolver`
- public: `is_configured`, `resolve`
### class `NullVaultResolver`
- public: `is_configured`, `resolve`
- intern: `__init__`
### class `InMemoryVaultResolver`
- public: `put`, `is_configured`, `resolve`
- intern: `__init__`
- def `default_resolver`

## `fusion_hero_os/meta/working_memory.py`

### class `WorkingMemoryError`
- (Datenklasse / ohne Methoden)
### class `ActivationReport`
- public: `to_dict`
### class `WorkingMemorySpace`
- public: `slots`, `step_index`, `activate`, `step`, `activation`, `vector`, `norm`, `report`, `reset`
- intern: `__init__`, `_clip`

## `fusion_hero_os/methodology/connectors.py`

### class `BaseConnector`
- public: `available`, `status`
- intern: `__init__`, `_dry_run`, `_delegate`, `__repr__`
### class `GitHubConnector`
- public: `commit`, `tag`, `create_repo`
### class `DriveConnector`
- public: `upload`, `download`, `list_files`
### class `VercelConnector`
- public: `deploy`, `list_deployments`
### class `GmailConnector`
- public: `send`, `parse_replies`
### class `XAPIConnector`
- public: `search`, `trends`, `post`
- intern: `__init__`
### class `ConnectorRegistry`
- public: `default`, `register`, `get`, `inject`, `available`, `plan`
- def `_demo`

## `fusion_hero_os/methodology/core_modules.py`

### class `PeerReviewCoreModule`
- public: `review`, `report`
### class `_Stage`
- (Datenklasse / ohne Methoden)
### class `ErkenntnisprozessCoreModule`
- public: `current_stage`, `advance`, `is_complete`, `report`
- intern: `__init__`
### class `FormalClassification`
- (Datenklasse / ohne Methoden)
### class `FormalMathematicsCoreModule`
- public: `classify`, `report`
### class `V3_3StructureCoreModule`
- public: `skeleton`, `render_markdown`
### class `ArchivePlan`
- (Datenklasse / ohne Methoden)
### class `AutomaticArchivingCoreModule`
- public: `build_plan`
### class `Milestone`
- (Datenklasse / ohne Methoden)
### class `RoadmapCoreModule`
- public: `add`, `complete`, `next_steps`, `next_step`, `report`
- intern: `__init__`, `_deps_erfuellt`
- def `_selbsttest`

## `fusion_hero_os/methodology/knowledge.py`

### class `Module`
- (Datenklasse / ohne Methoden)
### class `Decision`
- (Datenklasse / ohne Methoden)
### class `Repo`
- (Datenklasse / ohne Methoden)
### class `FileVersion`
- (Datenklasse / ohne Methoden)
- def `get_decision`
- def `list_modules`
- def `_md_modules`
- def `as_markdown`

## `fusion_hero_os/modules/automatic_archiving.py`

### class `AutomaticArchivingCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/code_review.py`

### class `PeerReviewCoreModule`
- public: `process`, `peer_review`
- intern: `_evaluate`

## `fusion_hero_os/modules/conversation_context.py`

### class `ConversationTurn`
- (Datenklasse / ohne Methoden)
### class `ConversationContextCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/formal_mathematics.py`

### class `FormalMathematicsCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/generational_evolution.py`

### class `GenerationalEvolutionProtocolCoreModule`
- public: `process`, `status`
- intern: `__init__`, `_ensure_impl`

## `fusion_hero_os/modules/heroic_llm_ea/evolution.py`

### class `EvolutionConfig`
- (Datenklasse / ohne Methoden)
### class `EvolutionarySelector`
- public: `run_generation`
- intern: `__init__`

## `fusion_hero_os/modules/heroic_llm_ea/fitness.py`

- def `fitness_function`
- def `score_with_peer_review`

## `fusion_hero_os/modules/heroic_llm_ea/memory.py`

### class `ProposalRecord`
- public: `proposal_id`
### class `MutationMemory`
- public: `remember`, `elites`, `best`, `mutate_from_elite`, `snapshot`
- intern: `__init__`

## `fusion_hero_os/modules/heroic_llm_ea/orchestrator.py`

### class `HeroicLLMEAOrchestrator`
- public: `with_campfire_templates`, `process`, `peer_review`
- intern: `__init__`, `_score_proposal`, `_propose_once`, `_evolve_many`, `_provider_status`

## `fusion_hero_os/modules/heroic_llm_ea/providers.py`

### class `LLMProvider`
- public: `propose`
### class `StubLLMProvider`
- public: `propose`
### class `CallableLLMProvider`
- public: `propose`
- intern: `__init__`
### class `CampfireTemplateProvider`
- public: `propose`
- intern: `__init__`, `_load`

## `fusion_hero_os/modules/image_orchestrator/job_queue.py`

### class `JobStatus`
- (Datenklasse / ohne Methoden)
### class `ImageJob`
- public: `to_dict`
### class `ImageJobQueue`
- public: `create`, `update`, `get`, `list_recent`
- intern: `__init__`, `_trim`

## `fusion_hero_os/modules/image_orchestrator/orchestrator.py`

### class `HeroicImageOrchestrator`
- public: `set_provider`, `process`, `peer_review`
- intern: `__init__`, `_load_config`, `_build_pipeline`

## `fusion_hero_os/modules/image_orchestrator/pipeline.py`

### class `ImagePipeline`
- public: `run`
- intern: `__init__`

## `fusion_hero_os/modules/image_orchestrator/prompt_builder.py`

- def `build_prompt`
- def `validate_identity`

## `fusion_hero_os/modules/image_orchestrator/providers.py`

### class `ImageProvider`
- public: `render`
### class `DryRunImageProvider`
- public: `render`
### class `CallableImageProvider`
- public: `render`
- intern: `__init__`

## `fusion_hero_os/modules/image_orchestrator/rate_limiter.py`

### class `RateLimitConfig`
- (Datenklasse / ohne Methoden)
### class `TokenBucketRateLimiter`
- public: `allow`, `status`
- intern: `__init__`, `_prune`
### class `DualRateLimiter`
- public: `allow`, `status`
- intern: `__init__`

## `fusion_hero_os/modules/live_process_tracking.py`

### class `TrackedProcess`
- (Datenklasse / ohne Methoden)
### class `LiveProcessTrackingCoreModule`
- public: `process`, `snapshot`
- intern: `__init__`

## `fusion_hero_os/modules/mer.py`

### class `MERModule`
- public: `process`, `optimize`
- def `_clamp01`

## `fusion_hero_os/modules/phone_link.py`

### class `PhoneLinkCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/qubo_integration.py`

### class `QUBOIntegrationCoreModule`
- public: `process`
- intern: `__init__`

## `fusion_hero_os/modules/self_modify.py`

### class `SelfModifyCoreModule`
- public: `process`, `propose_evolution`, `history`
- intern: `__init__`, `_record_proposal`

## `fusion_hero_os/modules/timespace_token/bottleneck.py`

- def `build_competition_qubo`
- def `greedy_bottleneck_assignment`
- def `qubo_energy`

## `fusion_hero_os/modules/timespace_token/geometry.py`

### class `Timescale`
- (Datenklasse / ohne Methoden)
### class `TimespaceCoordinate`
- public: `distance_to`
### class `TimespaceManifold`
- public: `default`, `origin_for_depth`, `geometric_priority`, `neighbor_compression`

## `fusion_hero_os/modules/timespace_token/manager.py`

### class `TimespaceTrack`
- (Datenklasse / ohne Methoden)
### class `AllocationReport`
- public: `to_dict`
### class `TimespaceTokenManager`
- public: `allocate`, `allocate_with_report`, `evolve_from_feedback`
- intern: `__init__`, `_fidelity_boost`

## `fusion_hero_os/modules/timespace_token/module.py`

- def `_track_from_dict`
### class `TimespaceTokenCoreModule`
- public: `process`, `peer_review`
- intern: `__init__`

## `fusion_hero_os/modules/weltraudaimonia.py`

### class `WeltraudaimoniaModule`
- public: `process`
- def `_clamp01`

## `fusion_hero_os/orchestration/agents.py`

### class `Message`
- (Datenklasse / ohne Methoden)
### class `MessageBus`
- public: `subscribe`, `publish`, `update_status`, `latest_status`, `all_status`, `history`
- intern: `__init__`
### class `Task`
- (Datenklasse / ohne Methoden)
### class `TaskQueue`
- public: `put`, `get_nowait`, `depth`, `empty`
- intern: `__init__`
- def `default_executor`
### class `Agent`
- public: `start`, `stop`, `join`, `shutdown`, `spawn_subagent`, `dismiss`, `children`, `assign`
- intern: `__init__`, `_post_heartbeat`, `_run`
### class `Supervisor`
- public: `summarize`, `run_until_drained`, `report`
- intern: `__init__`, `_hire`, `_fire_one_idle`, `_least_loaded`, `_outstanding`, `_run`, `_supervise`
- def `_demo`

## `fusion_hero_os/providers/base.py`

### class `LLMResult`
- public: `to_dict`
### class `BaseLLMProvider`
- public: `is_available`, `generate`, `health`
- intern: `__init__`, `_record`

## `fusion_hero_os/providers/claude_provider.py`

### class `ClaudeProvider`
- public: `is_available`, `generate`
- intern: `__init__`

## `fusion_hero_os/providers/everyapi_provider.py`

### class `EveryAPIProvider`
- public: `is_available`, `generate`
- intern: `__init__`

## `fusion_hero_os/providers/grok_provider.py`

### class `GrokProvider`
- public: `is_available`, `generate`
- intern: `__init__`

## `fusion_hero_os/providers/internal_provider.py`

### class `InternalFallbackProvider`
- public: `is_available`, `generate`
- intern: `__init__`, `_build_heroic_context`

## `fusion_hero_os/registry.py`

### class `ModuleStatus`
- (Datenklasse / ohne Methoden)
### class `ModuleUnavailableError`
- (Datenklasse / ohne Methoden)
### class `ModuleSpec`
- (Datenklasse / ohne Methoden)
### class `Registry`
- public: `load`, `load_all`, `get`, `try_get`, `status_report`
- intern: `__init__`
- def `get_registry`
- def `load_all`
- def `get`
- def `status_report`
- def `_print_status_report`

