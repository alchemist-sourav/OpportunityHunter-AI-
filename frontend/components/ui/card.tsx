export default function Card({
  title,
  children,
}: {
  title: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-2 text-lg font-semibold text-slate-900">{title}</h3>
      <div className="text-sm leading-relaxed text-slate-600">{children}</div>
    </div>
  );
}