export default function ComingSoon({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <section className="mx-auto max-w-3xl px-4 py-16 md:py-24">
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-8 text-center">
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">
          Phase 1 placeholder
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="mx-auto mt-3 max-w-xl text-slate-700">{description}</p>
      </div>
    </section>
  );
}
