export default function AuthPlaceholder({
  heading,
  action,
  fields,
}: {
  heading: string;
  action: string;
  fields: { label: string; type: string }[];
}) {
  return (
    <section className="mx-auto max-w-md px-4 py-16 md:py-24">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{heading}</h1>
        <p className="mt-2 text-sm text-slate-500">
          Authentication is not operational yet. This is a Phase 1 foundation placeholder.
        </p>
        <form className="mt-6 space-y-4" aria-disabled="true">
          {fields.map((field) => (
            <div key={field.label}>
              <label className="block text-sm font-medium text-slate-700">{field.label}</label>
              <input
                type={field.type}
                disabled
                placeholder="Disabled in Phase 1"
                className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-400"
              />
            </div>
          ))}
          <button
            type="submit"
            disabled
            className="w-full rounded-lg bg-indigo-300 px-4 py-2 text-sm font-medium text-white"
          >
            {action}
          </button>
        </form>
      </div>
    </section>
  );
}
