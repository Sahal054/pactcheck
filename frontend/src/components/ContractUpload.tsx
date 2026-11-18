import { FileText, Play } from 'lucide-react';

interface ContractUploadProps {
  filename: string;
  documentType: string;
  onTypeChange: (type: string) => void;
  onFile: (file: File) => Promise<void>;
  onReview: () => Promise<void>;
  busy: boolean;
  disabled: boolean;
}

const DOC_TYPES = ['MSA', 'NDA', 'DPA', 'SOW', 'SLA', 'Vendor Agreement'];

export default function ContractUpload({
  filename,
  documentType,
  onTypeChange,
  onFile,
  onReview,
  busy,
  disabled,
}: ContractUploadProps) {
  return (
    <section className="panel">
      <div className="panelhead">
        <div>
          <span className="eyebrow">AGREEMENT INTAKE</span>
          <h2>Upload contract</h2>
        </div>
        <FileText size={21} />
      </div>

      <label className="filebutton">
        {filename ? `Selected: ${filename}` : 'Choose contract (.pdf, .docx, .txt)'}
        <input
          type="file"
          accept=".pdf,.docx,.doc,.txt"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void onFile(file);
          }}
        />
      </label>

      <label className="fieldlabel">
        Document classification
        <select
          className="textinput"
          value={documentType}
          disabled={busy}
          onChange={(e) => onTypeChange(e.target.value)}
        >
          {DOC_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <button
        className="primary"
        disabled={busy || disabled}
        onClick={() => void onReview()}
      >
        <Play size={16} />
        {busy ? 'Processing...' : 'Run contract review'}
      </button>
    </section>
  );
}