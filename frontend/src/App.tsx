import { useState } from 'react';
import Sidebar, { type Section } from './components/Sidebar';
import PlaybookDashboard from './components/PlaybookDashboard';
import Dashboard from './pages/Dashboard';
import CrossClauseView from './components/CrossClauseView';
import RevisionCompare from './components/RevisionCompare';
import SettingsView from './components/SettingsView';
import type { ReviewReport } from './types/api';

export default function App() {
  const [active, setActive] = useState<Section>('Overview');
  const [report, setReport] = useState<ReviewReport | null>(null);
  return <div className="shell"><Sidebar active={active} onChange={setActive}/><main className="main">
    <div hidden={active !== 'Overview' && active !== 'Contract review'}><Dashboard report={report} onReportUpdate={setReport}/></div>
    {active === 'Playbook rules' && <PlaybookDashboard/>}
    {active === 'Cross-clause intelligence' && <CrossClauseView report={report} onReview={()=>setActive('Contract review')}/>}
    {active === 'Revision comparison' && <RevisionCompare/>}
    {active === 'Settings' && <SettingsView/>}
  </main></div>;
}
