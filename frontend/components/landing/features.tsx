import Card from "@/components/ui/card";

const features = [
  {
    title: "Your key, your control",
    body: "Each user supplies their own Firecrawl API key. Keys are stored encrypted on the server and never exposed to the browser.",
  },
  {
    title: "Private by design",
    body: "Credentials stay server-side. Opportunity scans run under your own key, and results are tied to your account only.",
  },
  {
    title: "Free-tier first",
    body: "Built to run on PostgreSQL and Supabase free tiers, with a self-hostable FastAPI backend and a Next.js frontend.",
  },
  {
    title: "Open source",
    body: "Licensed under Apache-2.0. Inspect it, self-host it, and contribute without vendor lock-in.",
  },
];

export default function Features() {
  return (
    <section className="border-t border-slate-100 bg-slate-50/60">
      <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
        <h2 className="text-center text-3xl font-semibold tracking-tight text-slate-900">
          Designed for independent hunters
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
          The foundation is built around privacy, low cost, and transparency.
        </p>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <Card key={feature.title} title={feature.title}>
              {feature.body}
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
