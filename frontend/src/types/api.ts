export interface Health {
  status: 'ok' | 'offline' | string;
  llm_provider?: string;
  embedding_provider?: string;
}

export interface IndexStatus {
  indexed: boolean;
  error?: string | null;
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
  created_at: string;
  contract_readiness_score: number;
  overall_risk: 'High' | 'Medium' | 'Low';
  rule_coverage: RuleCoverage[];
  contract_path?: string;
  document_type: string;
  total_clauses: number;
  risk_summary: Record<string, number>;
  clauses: ClauseAssessment[];
  cross_clause_findings: CrossClauseFinding[];
  negotiation_strategies: NegotiationStrategy[];
  disclaimer: string;
}
export interface RuleCoverage {
  rule_id: string;
  clause_type: string;
  status: 'Covered' | 'Partially Covered' | 'Not Covered';
  clause_ids: string[];
  explanation: string;
  policy: string;
  preferred_wording: string;
  requires_legal_review: boolean;
}

export interface RuntimeSettings {
  llm_provider: 'mock' | 'openai' | 'openrouter';
  llm_model: string;
  embedding_provider: 'local' | 'openai' | 'openrouter';
  embedding_model: string;
  api_keys_configured: {openai: boolean; openrouter: boolean};
}
export type SettingsUpdate = Partial<Omit<RuntimeSettings, 'api_keys_configured'>> & {
  openai_api_key?: string;
  openrouter_api_key?: string;
};
export interface DiagnosticResult {
  success: boolean;
  result?: {mode?: string; message?: string; connection?: string};
  dimensions?: number;
  provider?: string;
  model?: string;
}
export interface RevisionComparison {
  heading: string;
  status: string;
  original_clause_id?: string;
  revised_clause_id?: string;
  original_text?: string;
  revised_text?: string;
  new_risk_level?: ClauseAssessment['risk_level'];
  word_diff: DiffToken[];
  assessment?: ClauseAssessment;
  note?: string;
}
