import Button from "@/components/shared/button";

export default function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-20 text-center md:py-28">
      <p className="inline-block rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">
        Phase 1 · Foundation in progress
      </p>
      <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 md:text-6xl">
        Find your next opportunity before everyone else.
      </h1>
      <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
        OpportunityHunter AI will monitor grants, jobs, and growth signals that match your goals —
        privately, with your own API key, on a free-tier-friendly stack.
      </p>
      <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Button href="/register">Get early access</Button>
        <Button href="#how-it-works" variant="secondary">
          See how it works
        </Button>
      </div>
      <p className="mx-auto mt-8 max-w-2xl rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
        Authentication and opportunity discovery are not yet operational. This is the Phase 1
        application foundation.
      </p>
    </section>
  );
}
