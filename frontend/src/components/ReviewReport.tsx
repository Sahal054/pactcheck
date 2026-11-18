import { useState } from 'react';
import { Check, Copy, Download, Edit3, Eye, FileCheck, Mail, RotateCcw, Split, X } from 'lucide-react';
import { api } from '../services/api';
import type { ClauseAssessment, ReviewReport as Report } from '../types/api';

export default function ReviewReport({
  report,
  onReportUpdate,
}: {
  report: Report;
  onReportUpdate?: (updated: Report) => void;
}) {
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [diffMode, setDiffMode] = useState<'inline' | 'split'>('inline');
  const [editingClauseId, setEditingClauseId] = useState<string | null>(null);
  const [editText, setEditText] = useState<string>('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedEvidenceId, setExpandedEvidenceId] = useState<string | null>(null);

  const risks = ['High', 'Medium', 'Low', 'Unclear'];
  const filteredClauses = (report.clauses || []).filter(
    (c) => riskFilter === 'ALL' || c.risk_level === riskFilter
  );

  async function handleStatusChange(
    clause: ClauseAssessment,
    status: 'accepted' | 'rejected' | 'edited',
    customText?: string
  ) {
    try {
      const updated = await api.updateClauseRedline(
        report.review_id,
        clause.clause_id,
        status,
        customText
      );
      onReportUpdate?.(updated);
      setEditingClauseId(null);
    } catch (err) {
      console.error(err);
    }
  }

  function copyPushbackEmail(clause: ClauseAssessment) {
    const text =
      clause.counterparty_pushback_email ||
      `Regarding ${clause.clause_id} (${clause.heading}): ${clause.explanation}`;
    void navigator.clipboard.writeText(text);
    setCopiedId(clause.clause_id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  return (
    <section className="panel results">
      <div className="panelhead" style={{ flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <span className="eyebrow">REVIEW REPORT · {report.review_id.slice(0, 8)}</span>
          <h2>Docsum-Style Clause Redline & Playbook Workbench</h2>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            className="secondary"
            onClick={() => setDiffMode(diffMode === 'inline' ? 'split' : 'inline')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Split size={14} />
            {diffMode === 'inline' ? 'Switch to Split View' : 'Switch to Inline Git-Diff'}
          </button>
          <a
            href={api.exportDocxUrl(report.review_id)}
            className="primary"
            style={{ textDecoration: 'none' }}
            download
          >
            <Download size={15} />
            Export Redlined .DOCX (Track Changes)
          </a>
        </div>
      </div>

      {/* Risk Filter Scorecard */}
      <div className="riskgrid">
        {risks.map((r) => (
          <div
            key={r}
            onClick={() => setRiskFilter(riskFilter === r ? 'ALL' : r)}
            className={`riskstat risk-${r.toLowerCase()}`}
            style={{
              cursor: 'pointer',
              outline: riskFilter === r ? '2px solid #1e4569' : 'none',
            }}
          >
            <span>{r} risk (click to filter)</span>
            <b>{report.risk_summary?.[r] ?? 0}</b>
          </div>
        ))}
      </div>

      <div
        className="reportmeta"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          margin: '10px 0 16px',
        }}
      >
        <span>
          Showing <b>{filteredClauses.length}</b> of {report.total_clauses} clauses · Document Type:{' '}
          <b>{report.document_type}</b>
        </span>
        {riskFilter !== 'ALL' && (
          <button
            className="secondary"
            onClick={() => setRiskFilter('ALL')}
            style={{ padding: '4px 10px', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
          >
            <RotateCcw size={12} /> Show All Clauses
          </button>
        )}
      </div>

      <h3>Clause-by-Clause Playbook Evaluation & Visual Redliner</h3>
      {filteredClauses.map((c, i) => {
        const isEditing = editingClauseId === c.clause_id;
        const statusBadge = c.redline_status || 'pending';

        return (
          <article
            className="finding"
            key={c.clause_id || i}
            style={{
              borderLeft: `4px solid ${
                c.risk_level === 'High'
                  ? '#bf3c3c'
                  : c.risk_level === 'Medium'
                  ? '#d97706'
                  : '#218252'
              }`,
            }}
          >
            <div className="findingtop" style={{ flexWrap: 'wrap' }}>
              <div>
                <b>
                  {c.clause_id} · {c.heading}
                </b>
                <span className="muted" style={{ marginLeft: '10px', fontSize: '11px' }}>
                  ({c.compliance_status})
                </span>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {c.applicable_rule_ids?.map((rid) => (
                  <span key={rid} className="pill gray">
                    {rid}
                  </span>
                ))}
                <span
                  className={`pill ${
                    c.risk_level === 'High'
                      ? 'red'
                      : c.risk_level === 'Medium'
                      ? 'amber'
                      : c.risk_level === 'Low'
                      ? 'green'
                      : 'gray'
                  }`}
                >
                  {c.risk_level} risk
                </span>
              </div>
            </div>

            <p style={{ margin: '8px 0' }}>{c.explanation}</p>

            {/* Visual Git-Diff Redline Box */}
            {c.suggested_redline ? (
              <div
                className="redline"
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '14px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                    flexWrap: 'wrap',
                    gap: '8px',
                  }}
                >
                  <b
                    style={{
                      color: '#1e4569',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <FileCheck size={15} />
                    Proposed Playbook-Compliant Redline
                    {statusBadge === 'accepted' && <span className="pill green">Accepted</span>}
                    {statusBadge === 'edited' && <span className="pill green">Custom Edited</span>}
                    {statusBadge === 'rejected' && <span className="pill red">Rejected</span>}
                  </b>

                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    <button
                      className="secondary"
                      style={{
                        padding: '5px 10px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: statusBadge === 'accepted' ? '#dcfce7' : 'white',
                      }}
                      onClick={() => void handleStatusChange(c, 'accepted')}
                    >
                      <Check size={13} /> Accept
                    </button>
                    <button
                      className="secondary"
                      style={{
                        padding: '5px 10px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      onClick={() => {
                        setEditingClauseId(c.clause_id);
                        setEditText(c.suggested_redline || '');
                      }}
                    >
                      <Edit3 size={13} /> Edit
                    </button>
                    <button
                      className="secondary"
                      style={{
                        padding: '5px 10px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        background: statusBadge === 'rejected' ? '#fee2e2' : 'white',
                      }}
                      onClick={() => void handleStatusChange(c, 'rejected')}
                    >
                      <X size={13} /> Reject
                    </button>
                    <button
                      className="secondary"
                      style={{
                        padding: '5px 10px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                      onClick={() => copyPushbackEmail(c)}
                    >
                      {copiedId === c.clause_id ? <Check size={13} /> : <Copy size={13} />}
                      {copiedId === c.clause_id ? 'Copied Email!' : 'Copy Vendor Pushback Email'}
                    </button>
                  </div>
                </div>

                {isEditing ? (
                  <div style={{ marginTop: '10px' }}>
                    <textarea
                      className="textinput"
                      rows={4}
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      style={{ width: '100%', fontFamily: 'inherit' }}
                    />
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                      <button
                        className="primary"
                        onClick={() => void handleStatusChange(c, 'edited', editText)}
                      >
                        Save Custom Redline
                      </button>
                      <button className="secondary" onClick={() => setEditingClauseId(null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : diffMode === 'inline' && c.word_diff?.length ? (
                  <div
                    style={{
                      lineHeight: 1.7,
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      background: 'white',
                      padding: '12px',
                      borderRadius: '6px',
                      border: '1px solid #eef2f6',
                    }}
                  >
                    {c.word_diff.map((tok, idx) =>
                      tok.type === 'delete' ? (
                        <del
                          key={idx}
                          style={{
                            background: '#fee2e2',
                            color: '#991b1b',
                            textDecoration: 'line-through',
                            padding: '1px 2px',
                            borderRadius: '3px',
                          }}
                        >
                          {tok.text}
                        </del>
                      ) : tok.type === 'insert' ? (
                        <ins
                          key={idx}
                          style={{
                            background: '#dcfce7',
                            color: '#166534',
                            textDecoration: 'none',
                            fontWeight: 600,
                            padding: '1px 2px',
                            borderRadius: '3px',
                          }}
                        >
                          {tok.text}
                        </ins>
                      ) : (
                        <span key={idx}>{tok.text}</span>
                      )
                    )}
                  </div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div
                      style={{
                        background: '#fff5f5',
                        padding: '10px',
                        borderRadius: '6px',
                        border: '1px solid #fecaca',
                      }}
                    >
                      <small
                        style={{
                          color: '#991b1b',
                          fontWeight: 700,
                          display: 'block',
                          marginBottom: '4px',
                        }}
                      >
                        ORIGINAL VENDOR TEXT
                      </small>
                      <p style={{ margin: 0, fontSize: '12px' }}>{c.original_text}</p>
                    </div>
                    <div
                      style={{
                        background: '#f0fdf4',
                        padding: '10px',
                        borderRadius: '6px',
                        border: '1px solid #bbf7d0',
                      }}
                    >
                      <small
                        style={{
                          color: '#166534',
                          fontWeight: 700,
                          display: 'block',
                          marginBottom: '4px',
                        }}
                      >
                        PLAYBOOK-ALIGNED REDLINE
                      </small>
                      <p style={{ margin: 0, fontSize: '12px' }}>{c.suggested_redline}</p>
                    </div>
                  </div>
                )}

                {c.counterparty_pushback_email && (
                  <div
                    style={{
                      marginTop: '10px',
                      padding: '8px 12px',
                      background: '#eff6ff',
                      borderRadius: '6px',
                      fontSize: '12px',
                      color: '#1e3a8a',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <Mail size={14} style={{ flexShrink: 0 }} />
                    <span>
                      <b>Vendor Counsel Pushback Note:</b> "{c.counterparty_pushback_email}"
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div
                style={{
                  background: '#f8fafc',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  color: '#475569',
                }}
              >
                <b>Original Text:</b> {c.original_text}
              </div>
            )}

            {/* Retrieved RAG Playbook Evidence Accordion */}
            <div
              style={{
                marginTop: '10px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <small>
                Action: <b>{c.negotiation_action}</b>
              </small>
              {c.evidence?.length > 0 && (
                <button
                  className="secondary"
                  style={{
                    padding: '3px 8px',
                    fontSize: '11px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  onClick={() =>
                    setExpandedEvidenceId(expandedEvidenceId === c.clause_id ? null : c.clause_id)
                  }
                >
                  <Eye size={12} />{' '}
                  {expandedEvidenceId === c.clause_id
                    ? 'Hide Playbook Grounding'
                    : 'View Retrieved Playbook Rule'}
                </button>
              )}
            </div>

            {expandedEvidenceId === c.clause_id &&
              c.evidence?.map((ev, idx) => (
                <pre
                  key={idx}
                  style={{
                    marginTop: '8px',
                    background: '#0f172a',
                    color: '#e2e8f0',
                    padding: '12px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {ev.text}
                </pre>
              ))}
          </article>
        );
      })}

      {/* Cross-Clause Intelligence Section */}
      {report.cross_clause_findings?.length > 0 && (
        <>
          <h3>Cross-Clause Risk Intelligence</h3>
          {report.cross_clause_findings.map((f, i) => {
            const isHigh = f.risk_level === 'High';
            return (
              <article
                className="finding"
                key={f.finding_id || i}
                style={{
                  borderLeft: `4px solid ${isHigh ? '#bf3c3c' : '#d97706'}`,
                  background: isHigh ? '#fffafa' : '#fffdf7',
                }}
              >
                <div className="findingtop">
                  <b>
                    {f.finding_id} · {f.relationship}
                  </b>
                  <span className={`pill ${isHigh ? 'red' : 'amber'}`}>
                    {f.risk_level} Combined Risk
                  </span>
                </div>
                <p>{f.explanation}</p>
                <p style={{ color: '#1e4569', fontWeight: 600 }}>
                  Recommendation: {f.recommendation}
                </p>
                <small>Interacting Clauses: {f.related_clause_ids?.join(' ↔ ')}</small>
              </article>
            );
          })}
        </>
      )}

      <p className="muted disclaimer">{report.disclaimer}</p>
    </section>
  );
}