import Button from "@/components/shared/button";

export default function Cta() {
  return (
    <section className="border-t border-slate-100 bg-indigo-600">
      <div className="mx-auto max-w-3xl px-4 py-16 text-center md:py-20">
        <h2 className="text-3xl font-semibold tracking-tight text-white">
          OpportunityHunter AI is in Phase 1.
        </h2>
        <p className="mt-4 text-indigo-100">
          The backend, database layer, logging, security posture, and this frontend foundation are in
          place. Authentication and opportunity discovery arrive in later phases.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Button href="/register">Get early access</Button>
          <Button href="/dashboard" variant="secondary">
            View dashboard placeholder
          </Button>
        </div>
      </div>
    </section>
  );
}
