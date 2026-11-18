export interface Health {
  status: 'ok' | 'offline' | string;
  llm_provider?: string;
  embedding_provider?: string;
}

export interface IndexStatus {
  indexed: boolean;
  index_path?: string;
  rule_count?: number;
  playbook_path?: string;
}

export interface UploadedFile {
  contract_id?: string;
  filename: string;
  path: string;
}

export interface IndexResult {
  success: boolean;
  indexed_rules: number;
}

export interface DiffToken {
  type: 'equal' | 'delete' | 'insert';
  text: string;
}

export interface EvidenceChunk {
  rule_id: string;
  source: string;
  text: string;
}

export interface ClauseAssessment {
  clause_id: string;
  clause_number?: string;
  heading: string;
  page_start: number;
  page_end: number;
  original_text: string;
  risk_level: 'High' | 'Medium' | 'Low' | 'Unclear';
  compliance_status: string;
  applicable_rule_ids: string[];
  explanation: string;
  suggested_redline: string | null;
  redline_status?: 'pending' | 'accepted' | 'edited' | 'rejected';
  word_diff?: DiffToken[];
  negotiation_action: string;
  counterparty_pushback_email?: string | null;
  requires_legal_review: boolean;
  evidence: EvidenceChunk[];
  analysis_mode?: string;
}

export interface CrossClauseFinding {
  finding_id: string;
  related_clause_ids: string[];
  risk_level: 'High' | 'Medium' | 'Low' | 'Unclear';
  relationship: string;
  explanation: string;
  recommendation: string;
  requires_legal_review: boolean;
  basis: string;
}

export interface NegotiationStrategy {
  clause_id: string;
  rule_id: string | null;
  preferred_position: string;
  preferred_wording: string | null;
  fallback_position: string;
  escalation_conditions: string;
  walk_away_conditions: string;
  rationale: string;
  requires_legal_review: boolean;
}

export interface ReviewReport {
  review_id: string;
  contract_path?: string;
  document_type: string;
  total_clauses: number;
  risk_summary: Record<string, number>;
  clauses: ClauseAssessment[];
  cross_clause_findings: CrossClauseFinding[];
  negotiation_strategies: NegotiationStrategy[];
  disclaimer: string;
}