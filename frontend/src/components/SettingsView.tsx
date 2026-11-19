import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { RuntimeSettings, DiagnosticResult } from '../types/api';

export default function SettingsView() {
  const [settings,setSettings] = useState<RuntimeSettings | null>(null);
  const [openaiKey,setOpenaiKey] = useState('');
  const [routerKey,setRouterKey] = useState('');
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [message,setMessage] = useState('');
  const [diagnostics,setDiagnostics] = useState<{llm?: DiagnosticResult; embeddings?: DiagnosticResult}>({});
  useEffect(()=>{api.settings().then(setSettings).catch(e=>setError(e.message));},[]);
  async function save() {
    if (!settings) return;
    setBusy(true);setError('');setMessage('');setDiagnostics({});
    try {const result = await api.updateSettings({...settings, openai_api_key: openaiKey || undefined, openrouter_api_key: routerKey || undefined});
      setSettings(result);setOpenaiKey('');setRouterKey('');setMessage('Settings saved for this backend session. Rebuild the playbook index after changing embeddings.');
    } catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function test(kind: 'llm' | 'embeddings') {
    setBusy(true);setError('');
    try {const result = await (kind === 'llm' ? api.testLLM() : api.testEmbeddings());setDiagnostics(d=>({...d,[kind]:result}));}
    catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  return <><header><div><span className="eyebrow">PROVIDERS & CONNECTIVITY</span><h1>Settings & Diagnostics</h1><p>Configure review models and inspect live connection results. Save changes before testing.</p></div></header>
    {error && <p className="alert error" role="alert">{error}</p>}{message && <p className="alert success" role="status">{message}</p>}
    {!settings ? <section className="panel"><p>{error ? 'Settings could not be loaded. Check the backend connection and reopen this view.' : 'Loading provider settings…'}</p></section> : <section className="panel">
      <div className="splitgrid"><div><h2>Clause review</h2><label className="fieldlabel">LLM provider<select value={settings.llm_provider} onChange={e=>setSettings({...settings,llm_provider:e.target.value as RuntimeSettings['llm_provider'],llm_model:e.target.value === 'openai' ? 'gpt-4o-mini' : e.target.value === 'openrouter' ? 'openrouter/free' : 'deterministic-rules-v1'})}>{['mock','openai','openrouter'].map(x=><option key={x}>{x}</option>)}</select></label>
        <label className="fieldlabel">LLM model<input className="textinput" value={settings.llm_model} onChange={e=>setSettings({...settings,llm_model:e.target.value})}/></label></div>
        <div><h2>Playbook retrieval</h2><label className="fieldlabel">Embedding provider<select value={settings.embedding_provider} onChange={e=>setSettings({...settings,embedding_provider:e.target.value as RuntimeSettings['embedding_provider'], embedding_model: e.target.value === 'local' ? 'sentence-transformers/all-MiniLM-L6-v2' : e.target.value === 'openai' ? 'text-embedding-3-small' : ''})}>{['local','openai','openrouter'].map(x=><option key={x}>{x}</option>)}</select></label>
        <label className="fieldlabel">Embedding model<input className="textinput" value={settings.embedding_model} onChange={e=>setSettings({...settings,embedding_model:e.target.value})}/></label></div></div>
      <div className="splitgrid"><label className="fieldlabel">OpenAI API key · {settings.api_keys_configured.openai ? 'Configured' : 'Not configured'}<input className="textinput" type="password" autoComplete="new-password" value={openaiKey} onChange={e=>setOpenaiKey(e.target.value)} placeholder="Enter a replacement key"/></label>
      <label className="fieldlabel">OpenRouter API key · {settings.api_keys_configured.openrouter ? 'Configured' : 'Not configured'}<input className="textinput" type="password" autoComplete="new-password" value={routerKey} onChange={e=>setRouterKey(e.target.value)} placeholder="Enter a replacement key"/></label></div>
      <div className="actions"><button className="primary" onClick={()=>void save()} disabled={busy}>Save settings</button><button className="secondary" onClick={()=>void test('llm')} disabled={busy}>Test LLM Connection</button><button className="secondary" onClick={()=>void test('embeddings')} disabled={busy}>Test Embeddings</button></div>
      <p className="muted">Runtime changes apply immediately. Configure backend/.env for persistence across restarts. Local embeddings use cached MiniLM or deterministic 384-dimensional feature hashing when unavailable.</p>
      {Object.entries(diagnostics).map(([kind,result])=><div className="finding" role="status" key={kind}><b>{kind === 'llm' ? 'LLM connection' : 'Embedding connection'}: {result.success ? 'Success' : 'Failed'}</b><p>{result.result?.message || result.result?.connection || `${result.dimensions} dimensions · ${result.provider} · ${result.model}`}</p></div>)}
    </section>}
  </>;
}
