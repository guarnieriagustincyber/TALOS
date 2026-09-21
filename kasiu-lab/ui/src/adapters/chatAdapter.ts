import { GroundedEvidence, CitationItem } from '@domain/types';

export interface BackendCitationItem {
  evidence_id: string;
  document_hash: {
    algorithm: string;
    digest: string;
  };
  document_title: string;
  location: {
    page_start: number;
    page_end: number;
    section?: string;
  };
  verified_text_chunk: string;
  audit_status: string;
  rrf_score: number;
}

export interface BackendClaimAudit {
  claim_text: string;
  evidence_id: string;
}

export interface BackendChatResponse {
  reply_text: string;
  claims: BackendClaimAudit[];
  citation_manifest: Record<string, BackendCitationItem>;
  mermaid_diagram?: string | null;
  abstained: boolean;
  abstention_reason?: string | null;
}

export function adaptBackendChatResponse(raw: BackendChatResponse): {
  reply_text: string;
  evidences: GroundedEvidence[];
  mermaid_diagram?: string | null;
  abstained: boolean;
  abstention_reason?: string | null;
} {
  const evidences: GroundedEvidence[] = raw.claims.map((claim) => {
    const rawCit = raw.citation_manifest[claim.evidence_id];
    const citations: CitationItem[] = rawCit
      ? [
          {
            id: rawCit.evidence_id,
            source_hash: `${rawCit.document_hash.algorithm}:${rawCit.document_hash.digest}`,
            source_title: rawCit.document_title,
            location: {
              page_number: rawCit.location.page_start,
              snippet_quote: rawCit.verified_text_chunk,
            },
          },
        ]
      : [];

    return {
      evidence_id: claim.evidence_id,
      claim_text: claim.claim_text,
      citations,
      verification_score: rawCit ? rawCit.rrf_score : 0.0,
    };
  });

  return {
    reply_text: raw.reply_text,
    evidences,
    mermaid_diagram: raw.mermaid_diagram,
    abstained: Boolean(raw.abstained),
    abstention_reason: raw.abstention_reason || null,
  };
}
