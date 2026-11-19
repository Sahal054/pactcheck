import { useState } from 'react';
import { api } from '../services/api';
import type { RevisionComparison } from '../types/api';
import { WordDiff } from './ReviewReport';

export default function RevisionCompare() {
  const [original, setOriginal] = useState<File | null>(null);
  const [revised, setRevised] = useState<File | null>(null);
  const [docType, setDocType] = useState('MSA');
  const [rows, setRows] = useState<RevisionComparison[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [note, setNote] = useState('');
  async function compare() {
    if (!original || !revised) return;
    setBusy(true); setError(''); setRows([]); setNote('');
    try {
      const [a,b] = await Promise.all([api.uploadContract(original), api.uploadContract(revised)]);
      const result = await api.compare(a.path,b.path,docType);
      setRows(result.comparisons); setNote(result.note);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <><header><div><span className="eyebrow">NEGOTIATION PROGRESS</span><h1>Revision Comparison</h1><p>Compare vendor changes and re-assess revised language against the active playbook.</p></div></header>
    <section className="panel"><div className="splitgrid">
      <label className="dropzone">Original Contract<input aria-label="Original Contract" type="file" accept=".pdf,.docx,.md,.txt" disabled={busy} onChange={e=>setOriginal(e.target.files?.[0] || null)}/></label>
      <label className="dropzone">Revised Vendor Contract<input aria-label="Revised Vendor Contract" type="file" accept=".pdf,.docx,.md,.txt" disabled={busy} onChange={e=>setRevised(e.target.files?.[0] || null)}/></label>
    </div><div className="rowcontrols"><label>Document classification<select value={docType} onChange={e=>setDocType(e.target.value)} disabled={busy}>{['MSA','NDA','DPA','SOW','SLA'].map(x=><option key={x}>{x}</option>)}</select></label>
      <button className="primary" onClick={()=>void compare()} disabled={busy || !original || !revised}>{busy ? 'Comparing and assessing…' : 'Compare revisions'}</button></div></section>
    {error && <p className="alert error" role="alert">{error}</p>}
    {note && <section className="panel results"><p className="muted">{note}</p><div className="tablewrap"><table className="comparisons"><thead><tr><th>Clause</th><th>Assessment</th><th>Vendor changes</th></tr></thead><tbody>
      {rows.map((row,i)=><tr key={i}><td><b>{row.heading}</b><p className="tiny">{row.original_clause_id || 'New clause'} → {row.revised_clause_id || 'Removed'}</p></td>
        <td><span className={`pill ${row.status.startsWith('Resolved') ? 'green' : row.status.startsWith('Changed') || row.status === 'Removed' ? 'amber' : 'gray'}`}>{row.status}</span><p>{row.new_risk_level}</p><p>{row.assessment?.explanation || row.note}</p></td>
        <td><WordDiff tokens={row.word_diff}/></td></tr>)}
    </tbody></table></div></section>}
  </>;
}
