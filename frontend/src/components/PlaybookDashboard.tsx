import { useEffect, useState } from 'react';
import { AlertOctagon, BookOpen, CheckCircle2, Copy, Check, FileText, Search, ShieldAlert } from 'lucide-react';
import { BASE_URL } from '../services/api';

export interface PlaybookRuleItem {
  rule_id: string;
  clause_type: string;
  policy: string;
  red_flags: string[];
  preferred_wording: string;
  fallback_wording?: string | null;
  applicable_documents: string[];
  escalation_conditions: string[];
  source: string;
}

export default function PlaybookDashboard() {
  const [rules, setRules] = useState<PlaybookRuleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [docFilter, setDocFilter] = useState<'ALL' | 'MSA' | 'NDA'>('ALL');
  const [copiedRuleId, setCopiedRuleId] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${BASE_URL}/api/playbook/rules`)
      .then((res) => res.json())
      .then((data) => setRules(data.rules || []))
      .catch(() => setRules([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = rules.filter((r) => {
    const matchesDoc =
      docFilter === 'ALL' ||
      (r.applicable_documents || []).some((d) => d.toUpperCase() === docFilter);
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      r.rule_id.toLowerCase().includes(q) ||
      r.clause_type.toLowerCase().includes(q) ||
      r.policy.toLowerCase().includes(q) ||
      r.preferred_wording.toLowerCase().includes(q);
    return matchesDoc && matchesSearch;
  });

  function copyWording(rule: PlaybookRuleItem) {
    void navigator.clipboard.writeText(rule.preferred_wording);
    setCopiedRuleId(rule.rule_id);
    setTimeout(() => setCopiedRuleId(null), 2000);
  }

  return (
    <>
      <header>
        <div>
          <span className="eyebrow">KNOWLEDGE BASE & POLICY GOVERNANCE</span>
          <h1>Legal Negotiation Playbook Dashboard</h1>
          <p>
            Active RAG vector & BM25 rule repository governing automated contract redlining and risk scoring.
          </p>
        </div>
        <div className="topright">
          <span className="pill green">{rules.length} Active Playbook Rules</span>
        </div>
      </header>

      {/* Summary KPI Bar */}
      <section className="stats">
        <div className="stat">
          <span>Total Indexed Rules</span>
          <b>{rules.length} Rules</b>
          <small>Hybrid FAISS + BM25 Index</small>
        </div>
        <div className="stat">
          <span>MSA Coverage</span>
          <b>{rules.filter((r) => r.applicable_documents?.includes('MSA')).length} Rules</b>
          <small>Master Services Agreements</small>
        </div>
        <div className="stat">
          <span>NDA Coverage</span>
          <b>{rules.filter((r) => r.applicable_documents?.includes('NDA')).length} Rules</b>
          <small>Non-Disclosure Agreements</small>
        </div>
        <div className="stat">
          <span>Total Red-Flag Triggers</span>
          <b>{rules.reduce((acc, r) => acc + (r.red_flags?.length || 0), 0)} Triggers</b>
          <small>Automated High-Risk Patterns</small>
        </div>
      </section>

      {/* Search & Document Type Filter Bar */}
      <section className="panel" style={{ marginBottom: '18px', padding: '16px 22px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
            <Search size={16} color="#64748b" />
            <input
              className="textinput"
              style={{ marginTop: 0 }}
              placeholder="Search by Rule ID (e.g., RULE_001), clause type, policy, or wording..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {(['ALL', 'MSA', 'NDA'] as const).map((tab) => (
              <button
                key={tab}
                className={docFilter === tab ? 'primary' : 'secondary'}
                onClick={() => setDocFilter(tab)}
                style={{ padding: '8px 14px' }}
              >
                {tab === 'ALL' ? 'All Document Types' : `${tab} Rules`}
              </button>
            ))}
          </div>
        </div>
      </section>

      {loading ? (
        <section className="panel">
          <p className="muted">Loading indexed playbook rules...</p>
        </section>
      ) : filtered.length === 0 ? (
        <section className="panel">
          <p className="muted">No playbook rules match your filter. Make sure the playbook is indexed under Overview.</p>
        </section>
      ) : (
        <div style={{ display: 'grid', gap: '16px' }}>
          {filtered.map((rule) => (
            <section
              key={rule.rule_id}
              className="panel"
              style={{ borderLeft: '4px solid #1e4569' }}
            >
              <div className="panelhead" style={{ flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span className="pill" style={{ background: '#1e4569', color: 'white' }}>
                    {rule.rule_id}
                  </span>
                  <h2 style={{ margin: 0, textTransform: 'capitalize' }}>{rule.clause_type}</h2>
                </div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  {rule.applicable_documents?.map((doc) => (
                    <span key={doc} className="pill gray">
                      <FileText size={11} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                      {doc}
                    </span>
                  ))}
                </div>
              </div>

              {/* Official Corporate Policy */}
              <div style={{ marginBottom: '14px' }}>
                <span className="eyebrow">OFFICIAL CORPORATE POLICY</span>
                <p style={{ margin: '4px 0 0', fontSize: '13.5px', color: '#1e293b', lineHeight: 1.55, fontWeight: 500 }}>
                  {rule.policy}
                </p>
              </div>

              {/* 2-Column Grid: Red Flags vs Escalation & Fallback */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginBottom: '14px' }}>
                <div style={{ background: '#fff5f5', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px' }}>
                  <b style={{ color: '#991b1b', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                    <AlertOctagon size={14} />
                    Non-Compliant Red Flags (Auto High-Risk Triggers)
                  </b>
                  <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: '#7f1d1d', lineHeight: 1.6 }}>
                    {rule.red_flags?.map((rf, idx) => (
                      <li key={idx}>{rf}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '8px', padding: '12px' }}>
                  <b style={{ color: '#92400e', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                    <ShieldAlert size={14} />
                    Escalation Triggers & Fallback Position
                  </b>
                  <p style={{ margin: '0 0 6px', fontSize: '12px', color: '#78350f' }}>
                    <b>Escalation:</b> {rule.escalation_conditions?.join('; ') || 'Escalate any deviation to ABC Legal.'}
                  </p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#78350f' }}>
                    <b>Fallback:</b> {rule.fallback_wording || 'Requires explicit legal counsel sign-off.'}
                  </p>
                </div>
              </div>

              {/* Approved Standard Redline Wording */}
              <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '12px 14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
                  <b style={{ color: '#166534', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={14} />
                    Pre-Approved Standard Redline Wording (Drop-In Replacement)
                  </b>
                  <button
                    className="secondary"
                    style={{ padding: '4px 10px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    onClick={() => copyWording(rule)}
                  >
                    {copiedRuleId === rule.rule_id ? <Check size={12} /> : <Copy size={12} />}
                    {copiedRuleId === rule.rule_id ? 'Copied Wording!' : 'Copy Approved Clause'}
                  </button>
                </div>
                <p style={{ margin: 0, fontSize: '12.5px', color: '#14532d', fontFamily: 'monospace', lineHeight: 1.6 }}>
                  "{rule.preferred_wording}"
                </p>
              </div>
            </section>
          ))}
        </div>
      )}
    </>
  );
}