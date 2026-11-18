interface StatCardProps {
  label: string;
  value: string;
  note: string;
}

export default function StatCard({ label, value, note }: StatCardProps) {
  return (
    <div className="stat">
      <span>{label}</span>
      <b>{value}</b>
      <small>{note}</small>
    </div>
  );
}
