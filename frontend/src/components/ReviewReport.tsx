import { useState } from 'react';
import { Check, Copy, Download, Edit3, Eye, Mail, RotateCcw, Split, X } from 'lucide-react';
import { api } from '../services/api';
import { CoverageChecklist, CrossClauseFindings } from './CrossClauseView';
import type { ClauseAssessment, DiffToken, ReviewReport as Report } from '../types/api';

export function WordDiff({tokens}: {tokens?: DiffToken[]}) {
  return <div className="worddiff">{tokens?.map((token,i)=>token.type === 'delete' ? <del key={i}>{token.text}</del> : token.type === 'insert' ? <ins key={i}>{token.text}</ins> : <span key={i}>{token.text}</span>)}</div>;
}
export function ReadinessBanner({report}: {report: Report}) {
  return <div className="readiness" role="status"><div><span className="eyebrow">CONTRACT READINESS SCORE</span><strong>{report.contract_readiness_score}<small> / 100</small></strong></div>
    <div><span className={`pill ${report.overall_risk === 'High' ? 'red' : report.overall_risk === 'Medium' ? 'amber' : 'green'}`}>{report.overall_risk} overall risk</span><p className="muted">Clause findings, mandatory policy coverage and cross-clause interactions. Accepting a proposed redline does not re-assess the contract.</p></div></div>;
}
const riskColor = (risk: string) => risk === 'High' ? 'red' : risk === 'Medium' ? 'amber' : risk === 'Low' ? 'green' : 'gray';

export default function ReviewReport({report,onReportUpdate}: {report: Report; onReportUpdate: (updated: Report)=>void}) {
  const [riskFilter,setRiskFilter] = useState('ALL');
  const [diffMode,setDiffMode] = useState<'inline'|'split'>('inline');
  const [editing,setEditing] = useState<string | null>(null);
  const [editText,setEditText] = useState('');
  const [copied,setCopied] = useState<string | null>(null);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [expanded,setExpanded] = useState<string | null>(null);
  const clauses = report.clauses.filter(c=>riskFilter === 'ALL' || c.risk_level === riskFilter);
  async function update(c: ClauseAssessment, status: 'accepted'|'edited'|'rejected', custom?: string) {
    setBusy(true);setError('');
    try {const updated = await api.updateClauseRedline(report.review_id,c.clause_id,status,custom);onReportUpdate(updated);setEditing(null);}
    catch(e){setError((e as Error).message);} finally {setBusy(false);}
  }
  async function copy(c: ClauseAssessment) {
    setError('');
    try {await navigator.clipboard.writeText(c.counterparty_pushback_email || '');setCopied(c.clause_id);setTimeout(()=>setCopied(null),2000);}
    catch {setError('Clipboard access was unavailable. Select and copy the email text below.');}
  }
  return <section className="panel results"><div className="panelhead wrap"><div><span className="eyebrow">REVIEW REPORT · {report.review_id.slice(0,8)}</span><h2>Contract Redline & Playbook Workbench</h2></div>
    <div className="actions"><button className="secondary" onClick={()=>setDiffMode(diffMode === 'inline' ? 'split' : 'inline')}><Split size={14}/>{diffMode === 'inline' ? 'Switch to Split View' : 'Switch to Inline Git-Diff'}</button>
      <a className="primary" download href={api.exportDocxUrl(report.review_id)}><Download size={15}/>Export Redlined .DOCX (Track Changes)</a></div></div>
    <ReadinessBanner report={report}/>
    {error && <p className="alert error" role="alert">{error}</p>}
    <div className="riskgrid">{['High','Medium','Low','Unclear'].map(risk=><button key={risk} aria-pressed={riskFilter === risk} onClick={()=>setRiskFilter(riskFilter === risk ? 'ALL' : risk)} className={`riskstat risk-${risk.toLowerCase()} ${riskFilter === risk ? 'selected' : ''}`}><span>{risk} risk · Filter</span><b>{report.risk_summary[risk] || 0}</b></button>)}</div>
    <div className="findingtop"><p className="reportmeta">Showing {clauses.length} of {report.total_clauses} clauses · {report.document_type} · {report.created_at && new Date(report.created_at).toLocaleString()}</p>
      {riskFilter !== 'ALL' && <button className="secondary" onClick={()=>setRiskFilter('ALL')}><RotateCcw size={12}/>Show All Clauses</button>}</div>
    <h3>Clause-by-Clause Redlines</h3>
    {clauses.length === 0 && <p className="muted">No clauses in this risk category.</p>}
    {clauses.map(c=><article className={`finding clause-${c.risk_level.toLowerCase()}`} key={c.clause_id}>
      <div className="findingtop wrap"><b>{c.clause_number || c.clause_id} · {c.heading}</b><div className="actions">{c.applicable_rule_ids.map(r=><span className="pill gray" key={r}>{r}</span>)}<span className={`pill ${riskColor(c.risk_level)}`}>{c.risk_level} risk</span></div></div>
      <p><b>{c.compliance_status}</b> · {c.explanation}</p><small>Pages {c.page_start}–{c.page_end} · {c.analysis_mode}</small>
      {c.suggested_redline ? <div className="redline"><div className="findingtop wrap"><b>Proposed redline <span className="pill gray">{c.redline_status || 'pending'}</span></b>
        <div className="actions"><button disabled={busy} className="secondary" onClick={()=>void update(c,'accepted')}><Check size={13}/>Accept</button><button disabled={busy} className="secondary" onClick={()=>{setEditing(c.clause_id);setEditText(c.suggested_redline || '');}}><Edit3 size={13}/>Edit</button><button disabled={busy} className="secondary" onClick={()=>void update(c,'rejected')}><X size={13}/>Reject</button></div></div>
        {editing === c.clause_id ? <div><label className="fieldlabel">Replacement clause<textarea aria-label={`Replacement for ${c.heading}`} className="textinput" rows={6} value={editText} onChange={e=>setEditText(e.target.value)}/></label><div className="actions"><button className="primary" disabled={busy || !editText.trim()} onClick={()=>void update(c,'edited',editText)}>Save Edited Redline</button><button className="secondary" onClick={()=>setEditing(null)}>Cancel</button></div></div>
          : c.redline_status === 'rejected' ? <p>{c.original_text}</p>
          : diffMode === 'inline' ? <WordDiff tokens={c.word_diff}/> : <div className="splitgrid"><div className="original"><small>ORIGINAL VENDOR TEXT</small><p>{c.original_text}</p></div><div className="replacement"><small>PROPOSED REPLACEMENT</small><p>{c.suggested_redline}</p></div></div>}
      </div> : <div className="original"><p>{c.original_text}</p></div>}
      {c.counterparty_pushback_email && <div className="email"><div className="findingtop wrap"><b><Mail size={14}/> Vendor Counsel Pushback Email</b><button className="secondary" onClick={()=>void copy(c)}><Copy size={13}/>{copied === c.clause_id ? 'Copied' : 'Copy Vendor Pushback Email'}</button></div><p>{c.counterparty_pushback_email}</p></div>}
      <button className="secondary" aria-expanded={expanded === c.clause_id} onClick={()=>setExpanded(expanded === c.clause_id ? null : c.clause_id)}><Eye size={14}/>Retrieved Playbook Rule ({c.evidence.length})</button>
      {expanded === c.clause_id && <div className="grounding">{c.evidence.map(e=><div key={e.rule_id}><b>{e.rule_id} · {e.source}</b><pre>{e.text}</pre></div>)}</div>}
    </article>)}
    <CoverageChecklist report={report}/>
    <h3>Negotiation Strategy & Escalation Matrix</h3>
    {!report.negotiation_strategies.length && <p className="muted">No negotiation escalations recommended for assessed clauses.</p>}
    {report.negotiation_strategies.map(s=><details className="finding" key={s.clause_id}><summary>{s.clause_id} · {s.rule_id || 'Legal review'} · {s.preferred_position}</summary><p><b>Preferred wording:</b> {s.preferred_wording || 'Obtain approved wording from Legal.'}</p><p><b>Fallback:</b> {s.fallback_position}</p><p><b>Escalation:</b> {s.escalation_conditions}</p><p>{s.walk_away_conditions}</p><p>{s.rationale}</p></details>)}
    <CrossClauseFindings report={report}/><p className="muted disclaimer">{report.disclaimer}</p>
  </section>;
}
