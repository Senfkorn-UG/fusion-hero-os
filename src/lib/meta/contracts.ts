// Meta-neural vertical slice — API contract types.
//
// These mirror the pydantic models in
// `fusion_hero_os/meta/schemas.py`. Keep the two in sync. No field carries
// personal data: subjects are opaque ids only.

export type Purpose =
  | "ingest"
  | "working_memory"
  | "association"
  | "optimization"
  | "persistence"
  | "audit_read";

export type QUBOBackend = "auto" | "numpy" | "qb_qubo" | "rust" | "brute";

export interface ConsentGrantRequest {
  subject_id: string;
  purpose: Purpose;
  retention_days?: number; // default 30
}

export interface ConsentGrantResponse {
  grant_id: string;
  subject_id: string;
  purpose: Purpose;
  granted_at: string; // ISO-8601
  expires_at: string; // ISO-8601
  revoked_at: string | null;
  active: boolean;
}

export interface NodeFixture {
  node_id: string;
  type: string;
  dimensions?: Record<string, number>;
  attributes?: Record<string, unknown>;
}

export interface EdgeFixture {
  edge_id: string;
  type: string;
  source: string;
  target: string;
  weight?: number; // default 1.0
}

export interface IngestRequest {
  subject_id: string;
  grant_id: string;
  nodes: NodeFixture[];
  edges: EdgeFixture[];
}

export interface SnapshotResponse {
  snapshot_id: string;
  content_hash: string;
  schema_version: string;
  node_count: number;
  edge_count: number;
}

export interface ActivateRequest {
  subject_id: string;
  grant_id: string;
  activations: Record<string, number>;
  steps?: number; // default 1
}

export interface ActivationEntry {
  slot: string;
  activation: number;
}

export interface ActivationReportResponse {
  step_index: number;
  capacity: number;
  decay: number;
  active: ActivationEntry[];
}

export interface AssociateRequest {
  subject_id: string;
  grant_id: string;
}

export interface ConvergenceResponse {
  is_contraction: boolean;
  lipschitz_bound: number;
  spectral_radius: number;
  norm_order: string;
  note: string;
}

export interface OptimizeRequest {
  subject_id: string;
  grant_id: string;
  selection_dimension?: string; // default "salience"
  cardinality?: number | null;
  backend?: QUBOBackend; // default "numpy"
  seed?: number; // default 7
  steps?: number; // default 2000
}

export interface OptimizeResponse {
  objective: number;
  assignment: Record<string, number>;
  backend: string;
  seed: number;
  steps: number;
  constraints: Record<string, unknown>;
  source_snapshot: string;
  note: string;
}

export interface AuditEventResponse {
  seq: number;
  event_id: string;
  timestamp: string;
  action: string;
  subject_id: string | null;
  purpose: string | null;
  decision: "granted" | "denied" | "n/a";
  detail: Record<string, unknown>;
}

export interface AuditTrailResponse {
  chain_valid: boolean;
  events: AuditEventResponse[];
}
