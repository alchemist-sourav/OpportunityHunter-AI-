import Card from "@/components/ui/card";

const steps = [
  {
    step: "1",
    title: "You provide your API key",
    body: "Phase 2 will let you connect your own Firecrawl key, encrypted at rest on the server.",
    planned: true,
  },
  {
    step: "2",
    title: "Define what to hunt for",
    body: "Describe the grants, roles, or markets you care about. Phase 2 turns that into scheduled scans.",
    planned: true,
  },
  {
    step: "3",
    title: "Review matched opportunities",
    body: "Get a curated feed of matches in your dashboard. Phase 2 delivers the discovery pipeline.",
    planned: true,
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-16 md:py-24">
      <h2 className="text-center text-3xl font-semibold tracking-tight text-slate-900">
        How it will work
      </h2>
      <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
        The full flow arrives in Phase 2. What ships today is the secure foundation underneath it.
      </p>
      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {steps.map((item) => (
          <Card key={item.step} title={item.title}>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-indigo-600">
              Step {item.step} · Planned
            </p>
            {item.body}
          </Card>
        ))}
      </div>
    </section>
  );
}
