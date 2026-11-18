import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  GitCompareArrows,
  Network,
  RefreshCw,
  Scale,
  ShieldCheck,
} from 'lucide-react';
import ContractUpload from '../components/ContractUpload';
import ReviewReport from '../components/ReviewReport';
import StatCard from '../components/StatCard';
import { api } from '../services/api';
import type {
  Health,
  IndexStatus,
  ReviewReport as Report,
  UploadedFile,
} from '../types/api';

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [contract, setContract] = useState<UploadedFile | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [documentType, setDocumentType] = useState('MSA');
  const [playbookPath, setPlaybookPath] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const isConnected = health?.status === 'ok';

  async function refresh() {
    try {
      const [h, s] = await Promise.all([api.health(), api.indexStatus()]);
      setHealth(h);
      setIndexStatus(s);
    } catch {
      setHealth({ status: 'offline' });
      setIndexStatus(null);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function uploadContract(file: File) {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const uploaded = await api.uploadContract(file);
      setContract(uploaded);
      setReport(null);
      setMessage('Contract uploaded successfully.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function uploadPlaybook(file: File) {
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const result = await api.uploadPlaybook(file);
      setPlaybookPath(result.path);
      setMessage(`Playbook uploaded: ${result.filename}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function indexPlaybook() {
    if (!playbookPath.trim()) {
      setError('Upload a playbook or enter its backend-accessible path.');
      return;
    }
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const r = await api.indexPlaybook(playbookPath.trim());
      setMessage(`Indexed ${r.indexed_rules} playbook rules.`);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function runReview() {
    if (!contract?.path) return;
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const reviewResult = await api.review(contract.path, documentType);
      setReport(reviewResult);
      setMessage('Review completed.');
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <header>
        <div>
          <span className="eyebrow">ABC TECHNOLOGIES / LEGAL OPERATIONS</span>
          <h1>Contract intelligence workspace</h1>
          <p>
            Review vendor agreements, understand exposure and prepare
            negotiation positions.
          </p>
        </div>
        <div className="topright">
          <span className={`pill ${isConnected ? 'green' : 'gray'}`}>
            {isConnected ? 'API connected' : 'API offline'}
          </span>
          <button
            className="iconbtn"
            onClick={() => void refresh()}
            aria-label="Refresh status"
            disabled={busy}
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </header>

      <section className="stats">
        <StatCard
          label="LLM provider"
          value={health?.llm_provider || '—'}
          note="Configured backend"
        />
        <StatCard
          label="Embedding provider"
          value={health?.embedding_provider || '—'}
          note="Index and query model"
        />
        <StatCard
          label="Playbook index"
          value={
            indexStatus?.indexed
              ? `Ready${indexStatus.rule_count ? ` (${indexStatus.rule_count})` : ''}`
              : 'Not indexed'
          }
          note="Local FAISS + BM25"
        />
        <StatCard
          label="Review status"
          value={report ? 'Completed' : contract ? 'Ready to run' : 'Awaiting upload'}
          note="Current session"
        />
      </section>

      {error && (
        <div className="alert error" role="alert">
          <AlertTriangle size={17} />
          <span>{error}</span>
        </div>
      )}

      {message && (
        <div className="alert success" role="status">
          <CheckCircle2 size={17} />
          <span>{message}</span>
        </div>
      )}

      <div className="contentgrid">
        <div className="stack">
          <ContractUpload
            filename={contract?.filename || ''}
            documentType={documentType}
            onTypeChange={setDocumentType}
            onFile={uploadContract}
            onReview={runReview}
            busy={busy}
            disabled={!contract || !isConnected}
          />

          <section className="panel">
            <div className="panelhead">
              <div>
                <span className="eyebrow">KNOWLEDGE BASE</span>
                <h2>Legal negotiation playbook</h2>
              </div>
              <BookOpen size={21} />
            </div>
            <p className="muted">
              Upload your internal policy document, then build the searchable
              index before running a contract review.
            </p>
            <label className="filebutton">
              Choose playbook file
              <input
                type="file"
                accept=".pdf,.md,.txt"
                disabled={busy}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) void uploadPlaybook(file);
                }}
              />
            </label>
            <label className="fieldlabel">
              Or backend-accessible file path
              <input
                className="textinput"
                value={playbookPath}
                disabled={busy}
                onChange={(e) => setPlaybookPath(e.target.value)}
                placeholder="/path/to/legal_playbook.md"
              />
            </label>
            <button
              className="secondary"
              disabled={busy || !playbookPath.trim() || !isConnected}
              onClick={() => void indexPlaybook()}
            >
              Build / rebuild index
            </button>
            <p className="tiny muted">
              The path must exist on the backend machine. Uploading the file is
              easier for local use.
            </p>
          </section>
        </div>

        <section className="panel">
          <div className="panelhead">
            <div>
              <span className="eyebrow">INTELLIGENCE MODULES</span>
              <h2>Review capabilities</h2>
            </div>
            <Scale size={21} />
          </div>

          <div className="feature">
            <div className="featureicon">
              <Network />
            </div>
            <div>
              <b>Cross-clause risk intelligence</b>
              <p>
                Identify interactions such as indemnification exceptions
                bypassing liability caps.
              </p>
            </div>
          </div>

          <div className="feature">
            <div className="featureicon">
              <ShieldCheck />
            </div>
            <div>
              <b>Negotiation strategy</b>
              <p>
                Show preferred wording, fallback approval needs and escalation
                conditions.
              </p>
            </div>
          </div>

          <div className="feature">
            <div className="featureicon">
              <GitCompareArrows />
            </div>
            <div>
              <b>Vendor revision intelligence</b>
              <p>
                Revision comparison endpoint is available in the API; the UI
                workflow is not yet exposed.
              </p>
            </div>
          </div>

          <div className="notice">
            <AlertTriangle size={17} />
            <span>
              AI-assisted preliminary review only. Validate every finding and
              proposed redline with qualified legal counsel.
            </span>
          </div>
        </section>
      </div>

      {report && <ReviewReport report={report} />}
    </>
  );
}