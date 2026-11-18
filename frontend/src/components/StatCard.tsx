interface StatCardProps {
  label: string;
  value: string;
  note: string;
}

export default function StatCard({ label, value, note }: StatCardProps) {
  return (
    <div className="statcard">
      <span className="statlabel">{label}</span>
      <strong className="statvalue">{value}</strong>
      <span className="statnote">{note}</span>
    </div>
  );
}