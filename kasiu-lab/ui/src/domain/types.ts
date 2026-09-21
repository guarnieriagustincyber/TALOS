/**
 * Tipos de dominio de solo lectura sincronizados con FAC-0.1 y ADR-008
 */

export type HashDigest = string;

export interface CitationLocation {
  page_number: number;
  bbox?: [number, number, number, number];
  snippet_quote: string;
}

export interface CitationItem {
  id: string;
  source_hash: HashDigest;
  source_title: string;
  location: CitationLocation;
}

export interface GroundedEvidence {
  evidence_id: string;
  claim_text: string;
  citations: CitationItem[];
  verification_score: number;
}

export type SandboxFsmState =
  | 'IDLE'
  | 'READY'
  | 'EVALUATION_REQUESTED'
  | 'SANDBOX_RUNNING'
  | 'ASSESSMENT_RECEIVED'
  | 'PASSED'
  | 'FAILED'
  | 'ABSTAINED';

export interface PracticeAssertion {
  id: string;
  description: string;
  passed: boolean;
  error_message?: string;
}

export interface PracticeEvaluateResponse {
  exercise_id: string;
  fsm_state: SandboxFsmState;
  passed_assertions: number;
  total_assertions: number;
  assertions: PracticeAssertion[];
  ledger_block_hash?: HashDigest | null;
  timestamp_utc: string;
}
