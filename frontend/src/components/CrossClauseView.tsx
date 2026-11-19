import type { ReviewReport } from '../types/api';

export function CoverageChecklist({report}: {report: ReviewReport}) {
  return <section aria-label="Playbook coverage checklist">
    <h3>Missing Clause / Playbook Coverage Checklist</h3>
    {!report.rule_coverage?.length && <p className="notice">No applicable mandatory rules are indexed for this classification. Add relevant playbook rules before relying on readiness.</p>}
    {report.rule_coverage?.map(rule => <article className="finding" key={rule.rule_id}>
      <div className="findingtop"><b>{rule.rule_id} · {rule.clause_type}</b>
        <span className={`pill ${rule.status === 'Covered' ? 'green' : rule.status === 'Not Covered' ? 'red' : 'amber'}`}>{rule.status}</span></div>
      <p>{rule.explanation} {rule.clause_ids.join(', ')}</p>
      {rule.status !== 'Covered' && <details><summary>Policy and preferred position</summary><p>{rule.policy}</p><p>{rule.preferred_wording}</p></details>}
    </article>)}
  </section>;
}

export function CrossClauseFindings({report}: {report: ReviewReport}) {
  return <section aria-label="Cross-clause risk intelligence"><h3>Cross-Clause Risk Interactions</h3>
    {report.cross_clause_findings.length === 0 && <p className="muted">No interactions detected by the configured cross-clause checks.</p>}
    {report.cross_clause_findings.map(f => <article key={f.finding_id} className={`finding interaction ${f.risk_level.toLowerCase()}`}>
      <div className="findingtop"><b>{f.finding_id} · {f.relationship}</b><span className={`pill ${f.risk_level === 'High' ? 'red' : 'amber'}`}>{f.risk_level}</span></div>
      <p>{f.explanation}</p><p><b>Recommendation:</b> {f.recommendation}</p><small>{f.related_clause_ids.join(' · ')} · {f.basis}</small>
    </article>)}
  </section>;
}

export default function CrossClauseView({report, onReview}: {report: ReviewReport | null; onReview: () => void}) {
  return <><header><div><span className="eyebrow">DOCUMENT RISK INTELLIGENCE</span><h1>Cross-Clause & Coverage</h1><p>Review policy gaps and interactions across the whole agreement.</p></div></header>
    {report ? <section className="panel"><p className="reportmeta">Review {report.review_id.slice(0,8)} · {report.document_type} · {report.total_clauses} clauses</p>
      <CrossClauseFindings report={report}/><CoverageChecklist report={report}/></section> :
      <section className="panel"><h2>Start with a contract review</h2><p className="muted">Upload an agreement and analyze it against the playbook to see interactions and mandatory coverage.</p><button className="primary" onClick={onReview}>Go to Contract Review</button></section>}
  </>;
}
