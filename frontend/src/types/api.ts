export interface Health {
  status: 'ok' | 'offline' | string;
  llm_provider?: string;
  embedding_provider?: string;
}

export interface IndexStatus {
  indexed: boolean;
  rule_count?: number;
  playbook_path?: string;
}

export interface UploadedFile {
  filename: string;
  path: string;
}

export interface IndexResult {
  indexed_rules: number;
}

export interface ClauseFinding {
  id: string;
  clause_title: string;
  risk_level: 'high' | 'medium' | 'low';
  summary: string;
  cross_clause_notes?: string;
  preferred_wording?: string;
  fallback_position?: string;
  escalation_required?: boolean;
}

export interface ReviewReport {
  document_type: string;
  overall_risk: 'high' | 'medium' | 'low';
  executive_summary: string;
  findings: ClauseFinding[];
}