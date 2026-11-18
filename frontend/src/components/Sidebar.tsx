import { Activity, FileSearch, GitCompareArrows, Network, Settings, ShieldCheck } from 'lucide-react';
export type Section = 'Overview' | 'Contract review' | 'Cross-clause intelligence' | 'Revision comparison' | 'Settings';
const links = [
  { label: 'Overview' as const, icon: Activity },
  { label: 'Contract review' as const, icon: FileSearch },
  { label: 'Cross-clause intelligence' as const, icon: Network },
  { label: 'Revision comparison' as const, icon: GitCompareArrows },
  { label: 'Settings' as const, icon: Settings },
];
export default function Sidebar({ active, onChange }: { active: Section; onChange: (section: Section) => void }) {
  return <aside className="sidebar"><div className="brand"><div className="brandmark"><ShieldCheck size={22}/></div><div><b>ContractIQ</b><small>LEGAL INTELLIGENCE</small></div></div><div className="navlabel">WORKSPACE</div><nav>{links.map(({label, icon: Icon}) => <button key={label} className={`navitem ${active === label ? 'active' : ''}`} onClick={() => onChange(label)}><Icon size={17}/><span>{label}</span></button>)}</nav><div className="sidebottom"><span className="statusdot"/> Local development environment</div></aside>;
}
