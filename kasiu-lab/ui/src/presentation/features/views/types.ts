export type TopView = "chat" | "arbol" | "libros" | "ingesta" | "federacion" | "threatintel" | "telemetria" | "gates" | "config" | "tareas" | "agenda" | "estudiante";
export type EvidenceTab = "mermaid" | "grafo" | "pagina" | "fuente" | "packet" | "pcap" | "notas" | "sandbox" | "contradicciones" | "evidencia" | "progreso";
export type TaskColumn = "pendiente" | "haciendo" | "finalizadas" | "futuro";
export type TaskScopeType = "general" | "folder" | "notebook";

export interface KanbanSubtask {
  id: string;
  text: string;
  done: boolean;
}

export interface KanbanTask {
  id: string;
  title: string;
  description?: string;
  column: TaskColumn;
  priority: "P1" | "P2" | "P3";
  scope: string;
  scopeType?: TaskScopeType;
  deadline: string;
  isExpanded: boolean;
  subtasks: KanbanSubtask[];
}

export interface NoteItem {
  id: string;
  title: string;
  text: string;
  date: string;
  scope?: string;
  pinned?: boolean;
}

export interface Citation {
  id?: string;
  citationId: string;
  sourceId: string | null;
  source_id?: string | null;
  sourceTitle?: string;
  source_title?: string;
  page?: number | null;
  pageStart?: number | null;
  pageEnd?: number | null;
  chunkText?: string;
  chunk_text?: string;
  chunkId?: string | null;
  relevanceScore?: number;
  relevance_score?: number;
  docHash: string | null;
  authorityWeight?: number;
  namespace?: "E" | "TF" | "LAB";
  author?: string;
  section?: string;
  epistemicRole?: "pedagogical" | "formal" | "technical" | string;
  epistemic_role?: "pedagogical" | "formal" | "technical" | string;
}

export interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  isSaved?: boolean;
  errorState?: boolean;
  evidences?: Citation[];
  facetCoverage?: Record<string, "SUFFICIENT" | "PARTIAL" | "MISSING">;
  abstained?: boolean;
  abstentionReason?: string | null;
  claims?: ClaimItemDto[];
  edited?: boolean;
}

export interface MindMapNode {
  id: string;
  label: string;
  category: string;
  x: number;
  y: number;
  status: "completed" | "current" | "locked";
  connectedTo: string[];
  docRef: string;
  evalCmd: string;
  description: string;
}

export interface NotebookData {
  id: string;
  name: string;
  category: string;
  progress: number;
  totalHours: string;
  units: {
    number: number;
    title: string;
    status: "completed" | "in-progress" | "pending";
    progress: number;
    topics: string[];
  }[];
  mindMapNodes: MindMapNode[];
  exercises: {
    id: string;
    title: string;
    status: "approved" | "pending";
    desc: string;
  }[];
}

export interface FSItem {
  id: string;
  name: string;
  type: "folder" | "notebook";
  parentId: string | null;
  icon?: string;
  color?: string;
}

export interface FolderMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
}

export interface ActiveEntity {
  id: string;
  name: string;
  type: "folder" | "notebook" | "root";
  icon?: string;
  color?: string;
}

export interface RoadmapNodeDto {
  node_id: string;
  title: string;
  status: string;
  prerequisites: string[];
  is_root: boolean;
  node_type: string;
  subtopics?: string[];
  description?: string;
  unit?: number;
}

export interface RoadmapEdgeDto {
  from_node: string;
  to_node: string;
  dependency_type: string;
}

export interface RoadmapResponse {
  roadmap_id: string;
  title: string;
  nodes: RoadmapNodeDto[];
  edges: RoadmapEdgeDto[];
  mermaid_source: string;
}

export const INITIAL_FS: FSItem[] = [
  // Rama FADENA / 1erAño / 2doCuatrimestre
  { id: "fadena", name: "FADENA", type: "folder", parentId: null, icon: "shield", color: "emerald" },
  { id: "fadena_1ano", name: "1er Año", type: "folder", parentId: "fadena", icon: "folder", color: "emerald" },
  { id: "fadena_1ano_2cuat", name: "2do Cuatrimestre", type: "folder", parentId: "fadena_1ano", icon: "folder", color: "emerald" },
  { id: "fadena-lenguajes", name: "Lenguajes de Programación.nb", type: "notebook", parentId: "fadena_1ano_2cuat", icon: "terminal", color: "blue" },
  { id: "fadena-so2", name: "Sistemas Operativos II.nb", type: "notebook", parentId: "fadena_1ano_2cuat", icon: "cpu", color: "purple" },
  { id: "fadena-std", name: "Sistema de Tratamiento de Datos.nb", type: "notebook", parentId: "fadena_1ano_2cuat", icon: "database", color: "amber" },
  { id: "fadena-teleco", name: "Infraestructura de Telecomunicaciones.nb", type: "notebook", parentId: "fadena_1ano_2cuat", icon: "network", color: "rose" },
  { id: "fadena-sye", name: "Sociedad y Estado.nb", type: "notebook", parentId: "fadena_1ano_2cuat", icon: "shield", color: "emerald" },

  // Rama Roadmap / Fase0
  { id: "roadmap", name: "Roadmap", type: "folder", parentId: null, icon: "terminal", color: "amber" },
  { id: "roadmap_fase0", name: "Fase 0", type: "folder", parentId: "roadmap", icon: "shield", color: "emerald" },
  { id: "fase0-soc", name: "Programación y Pensamiento Algorítmico.nb", type: "notebook", parentId: "roadmap_fase0", icon: "terminal", color: "blue" },
];

export interface StudentMasteryNode {
  id: string;
  label: string;
  category: string;
  scope: string;
  status: "mastered" | "in_progress" | "weak";
  retentionScore: number; // 0-100
  lastReviewed: string;
}

export interface StudentStrength {
  id: string;
  topic: string;
  domain: string;
  score: number;
  assertionSnippet: string;
}

export interface StudentWeakness {
  id: string;
  topic: string;
  domain: string;
  gapDescription: string;
  recommendedDoc: string;
}

export interface StudentAlert {
  id: string;
  type: "critical" | "warning" | "info";
  title: string;
  desc: string;
  deadline?: string;
  actionLabel?: string;
}

export interface CompetencyDomain {
  name: string;
  score: number; // 0-100
  fullMark: number;
}

export interface BktKcStateDto {
  p_L: number;
  attempts: number;
  last_update: string;
}

export interface StudentActiveAlertDto {
  alert_id: string;
  kc_id: string;
  title: string;
  p_L: number;
  severity: "CRITICAL" | "WARNING" | string;
  detected_at: string;
}

export interface CognitiveStateResponse {
  kc_mastery: Record<string, BktKcStateDto>;
  active_alerts: StudentActiveAlertDto[];
  readiness_cache: Record<string, any>;
}

export interface SpacedRepetitionDueItem {
  anchor_id: string;
  topic_title: string;
  interval_days: number;
  due_date: string;
  ef: number;
  is_due: boolean;
}

export interface PrerequisiteReadinessDto {
  prereq_id: string;
  p_L: number;
  status: "DOMINADO" | "NOCIÓN" | "AUSENTE";
}

export interface ReadinessReportDto {
  target_topic_id: string;
  prerequisites: PrerequisiteReadinessDto[];
  recommendation: "START" | "START_WITH_SCAFFOLD" | "REMEDIATE_FIRST";
  notes: string[];
}

export interface RemediationRespondResponse {
  status: string;
  interrupt_id: string;
  choice: string;
  next_action: string;
}

export interface ClaimItemDto {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  criticality: string;
  status: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED" | "CONTRADICTION" | string;
  grounding_ratio: number;
  cited_evidence_indices: string[];
  has_redaction: boolean;
}

export interface ContradictionItemDto {
  claim_id: string;
  claim_text: string;
  source_a: string;
  assertion_a: string;
  source_b: string;
  assertion_b: string;
  conflict_type: string;
  status: string;
}

export interface ClaimsVerificationResponse {
  session_id: string;
  verdict: string;
  claims: ClaimItemDto[];
  redacted_text?: string | null;
  contradictions: ContradictionItemDto[];
}

export interface CoverageResponse {
  session_id: string;
  facets: Record<string, "SUFFICIENT" | "PARTIAL" | "MISSING" | string>;
  coverage_ratio: number;
  sufficient_count: number;
  partial_count: number;
  missing_count: number;
  status: string;
  grounding_rate: number;
  notes?: string;
}

// ==========================================
// FASE 4: CAL Ingesta, Federación & Threat Intel DTOs
// ==========================================

export interface CALSourceItemDto {
  source_id: string;
  title: string;
  author?: string;
  notebooks?: string[];
  doc_hash: string;
  chunk_count: number;
  converter_id: string;
  converter_version: string;
  conversion_score: number;
  conflict_flag: boolean;
  formulas_unextracted: boolean;
  trust_level: "verified" | "unverified" | string;
  ocr_provenance: "none" | "local_tesseract" | "cloud" | string;
  ingested_at: string;
}

export interface ConversionConflictDto {
  conflict_id: string;
  source_sha256: string;
  converter_a: string;
  converter_b: string;
  candidate_a_hash: string;
  candidate_b_hash: string;
  diff_stat: number;
  resolution: "PENDING" | "ADJUDICATED" | string;
  adjudicated_by?: string | null;
  created_at: string;
}

export interface ColabStatusDto {
  total_chunks: number;
  total_vectors: number;
  pending_chunks: number;
  rclone_installed: boolean;
  gdrive_configured: boolean;
  remote_path: string;
  latest_pending: string | null;
  latest_vectors: string | null;
}

export interface ColabExportDto {
  status: string;
  count: number;
  filename: string | null;
  download_url: string | null;
  gdrive_uploaded: boolean;
  gdrive_message: string | null;
  message: string;
}

export interface ColabSyncDto {
  status: string;
  synced: number;
  inserted: number;
  updated: number;
  pending_remaining: number;
  file_used: string | null;
  message: string;
}

export interface FederatedNotebookDto {
  notebook_id: string;
  name: string;
  subject: string;
  level: string;
  source_count: number;
  default_scope: "confined" | "federated" | string;
  created_at: string;
}

export interface FederationBridgeDto {
  bridge_id: string;
  source_notebook: string;
  target_notebook: string;
  topic_allowlist: string[];
  direction: "bidirectional" | "unidirectional" | string;
  ttl_days: number;
  created_at: string;
  expires_at: string;
  status: "ACTIVE" | "EXPIRED" | string;
  reviewer: string;
  provenance_tag: string;
}

export interface QuorumSummaryDto {
  feeds_agree: number;
  total_feeds: number;
}

export interface ThreatIntelIOCDto {
  ioc_id: string;
  type: "ip" | "domain" | "sha256" | "url" | string;
  value: string;
  verdict: "malicious" | "clean" | "suspicious" | "unknown" | string;
  trust_level: "unverified" | "verified_human" | string;
  quorum: QuorumSummaryDto;
  conflicts: string[];
  promoted_at?: string | null;
  promoter?: string | null;
  last_updated: string;
}

// ==========================================
// FASE 5: Telemetría E5, Gates & Configuración Read-Only
// ==========================================

export interface BenchmarkComparisonDto {
  benchmark_name: string;
  domain: string;
  n_samples: number;
  industry_baseline_sac: number;
  industry_baseline_eeu: number;
  talos_sac: number;
  talos_eeu: number;
  delta_sac_pp: number;
}

export interface TelemetryMetricsDto {
  sac: number;
  eeu_oracle: number;
  eeu_internal: number;
  redundancy_rate: number;
  far: number;
  fgr: number;
  raf: number;
  tp_abstain: number;
  fp_abstain: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  zero_llm_epistemic_calls: number;
  protocolary_comparisons: BenchmarkComparisonDto[];
  timestamp: string;
}

export interface GateVerificationDto {
  gate_id: string;
  name: string;
  layer: "E1" | "E2" | "E3" | "CAL" | "E4" | "E5" | string;
  status: "PASSED" | "CONDICIONAL" | "BLOCKED" | string;
  criteria: string;
  measured_value: string;
  threshold: string;
  pinned_commit: string;
  report_path: string;
  limitation_note?: string | null;
}

export interface FrozenPerimeterStatusDto {
  path: string;
  status: string;
  adr_rule: string;
}

export interface ReadOnlyConfigDto {
  bridges_allowlist: Record<string, any>;
  lab_kc_map: Record<string, any>;
  namespace_registry: Record<string, any>;
  routing_table_frozen: Record<string, any>;
  e1_category_policy: Record<string, any>;
  frozen_perimeters: FrozenPerimeterStatusDto[];
  adr_compliance: string;
  fetched_at: string;
}

export interface DomainDistributionItemDto {
  kc_id: string;
  kc_display_name: string;
  unit: string;
  chunk_count: number;
  percentage: number;
}

export interface DomainDistributionDto {
  notebook_id: string;
  total_chunks: number;
  distribution: DomainDistributionItemDto[];
}

export interface NotebookSourceItemDto {
  source_id: string;
  title: string;
  sha256: string;
  author: string;
  filename: string;
  page_count: number;
  chunk_count: number;
}

export interface NotebookSourcesResponseDto {
  notebook_id: string;
  total_sources: number;
  sources: NotebookSourceItemDto[];
}


