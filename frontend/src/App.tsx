import { useState } from 'react';
import Sidebar, { type Section } from './components/Sidebar';
import Dashboard from './pages/Dashboard';
export default function App() {
  const [active, setActive] = useState<Section>('Overview');
  return <div className="shell"><Sidebar active={active} onChange={setActive}/><main className="main">{active === 'Overview' || active === 'Contract review' ? <Dashboard/> : <section className="panel placeholder"><span className="eyebrow">{active.toUpperCase()}</span><h2>{active}</h2><p className="muted">This module is not implemented in the current backend/UI build. The core contract upload, playbook indexing and clause review workflow is available under Overview.</p><button className="primary" onClick={() => setActive('Overview')}>Return to overview</button></section>}</main></div>;
}
