import type { Metadata } from "next";
import Link from "next/link";

import MarketingShell from "@/components/MarketingShell";

export const metadata: Metadata = {
  title: "Pilot program",
  description:
    "Paid AISTruth pilots for fleet ops, charter desks, and coastal monitoring — API access, console, and explainable AIS integrity evidence.",
};

const INCLUDED = [
  {
    title: "Dedicated tenant & API key",
    text: "Named pilot environment with revocable credentials and usage metering for SOW enforcement.",
  },
  {
    title: "Validation API + console",
    text: "REST endpoints and an interactive map for ops briefings — motion heuristics, spoofing signals, GEODNET context.",
  },
  {
    title: "Your AIS feed (BYOK)",
    text: "Bring a permitted feed: Norwegian open AIS (BarentsWatch), Spire Maritime BYOK, or a licensed aggregator.",
  },
  {
    title: "Weekly pilot digest",
    text: "Validations run, alert-tier findings, and top MMSIs — enough to steer the pilot without full alerting on day one.",
  },
  {
    title: "Onboarding & check-ins",
    text: "Kickoff call, MMSI/watchlist setup, and bi-weekly reviews mapped to fleet, charter, or compliance workflows.",
  },
  {
    title: "Evidence export path",
    text: "Structured JSON today; printable one-pager reports for charter and dispute workflows as the pilot progresses.",
  },
];

const TIMELINE = [
  {
    n: "01",
    title: "Discovery & scope",
    text: "MMSIs, operating area, AIS source, and success criteria — fleet screening, charter evidence, or compliance sampling.",
  },
  {
    n: "02",
    title: "Kickoff & provisioning",
    text: "API key, console access, and initial watchlist — usually within a few business days of signed SOW.",
  },
  {
    n: "03",
    title: "Run & review",
    text: "Weekly digests, bi-weekly check-ins, quota tracking, and workflow feedback from your team (weeks 2–10).",
  },
  {
    n: "04",
    title: "Pilot report & renewal",
    text: "Summary of findings, usage, and a clear path to annual API access or expanded scope.",
  },
];

const NOT_INCLUDED = [
  "Centimetre-class RTK position claims or certified GNSS truth products",
  "Automated email/Slack alerting (manual weekly digest during pilot)",
  "Self-serve Stripe checkout — invoiced SOW for early pilots",
  "Redistribution of raw AIS beyond your feed entitlements",
];

const GEO = [
  {
    region: "Norwegian coastal waters",
    feed: "BarentsWatch open AIS",
    note: "Best for live demos and coastal screening in the Norwegian EEZ.",
  },
  {
    region: "Canada & international",
    feed: "Customer Spire BYOK or licensed AIS",
    note: "Production pilots run on your entitlements — we validate integrity, we do not resell AIS.",
  },
];

export default function PilotPage() {
  return (
    <MarketingShell active="pilot">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200/80 bg-white">
        <div
          className="pointer-events-none absolute -right-32 -top-32 h-80 w-80 rounded-full bg-gradient-to-br from-cyan-200/40 to-teal-100/30 blur-3xl"
          aria-hidden
        />
        <div className="relative mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-20">
          <p className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-700">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            Commercial pilot
          </p>
          <h1 className="mt-5 max-w-3xl text-3xl font-semibold leading-tight tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
            Defensible AIS integrity evidence — scoped, metered, and ready for ops.
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-slate-600">
            Typical engagement: <span className="font-semibold text-slate-800">8–12 weeks</span>, fixed validation
            quota, named vessels or watchlists, and deliverables your team can use in briefings — not a science project.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center justify-center rounded-xl bg-teal-600 px-6 py-3.5 text-sm font-semibold text-white shadow-lg shadow-teal-600/25 transition hover:bg-teal-500"
              href="/contact"
            >
              Request a pilot
            </Link>
            <Link
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50"
              href="/console"
            >
              Try the demo first
            </Link>
          </div>
        </div>
      </section>

      {/* Included */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">What&apos;s included</h2>
          <p className="mt-3 leading-relaxed text-slate-600">
            Everything needed to run a paid pilot with clear quotas, evidence your team can defend, and a path to
            production.
          </p>
        </div>
        <ul className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {INCLUDED.map((item) => (
            <li
              key={item.title}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300 hover:shadow-md"
            >
              <h3 className="text-base font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{item.text}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Geography */}
      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Geography &amp; AIS feeds</h2>
          <p className="mt-3 max-w-2xl leading-relaxed text-slate-600">
            The engine is feed-agnostic. Pilots are scoped to waters and data you are entitled to use commercially.
          </p>
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            {GEO.map((item) => (
              <div key={item.region} className="rounded-2xl border border-slate-200 bg-slate-50 p-6 sm:p-7">
                <h3 className="text-base font-semibold text-slate-900">{item.region}</h3>
                <p className="mt-2 text-sm font-medium text-teal-700">{item.feed}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{item.note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline + out of scope */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_0.8fr] lg:items-start">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Pilot timeline</h2>
            <p className="mt-3 max-w-xl leading-relaxed text-slate-600">
              A predictable sequence from discovery to renewal — designed for shipping teams, not research labs.
            </p>
            <ol className="mt-10 grid gap-8 sm:grid-cols-2">
              {TIMELINE.map((step) => (
                <li key={step.n}>
                  <span className="text-3xl font-bold tabular-nums text-teal-200">{step.n}</span>
                  <h3 className="mt-2 text-lg font-semibold text-slate-900">{step.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{step.text}</p>
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7 lg:sticky lg:top-24">
            <h2 className="text-lg font-semibold text-slate-900">Out of scope for early pilots</h2>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              Expectations set upfront so procurement and ops know exactly what they are buying.
            </p>
            <ul className="mt-6 space-y-3">
              {NOT_INCLUDED.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-relaxed text-slate-600">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" aria-hidden />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <div className="rounded-2xl border border-teal-200 bg-gradient-to-br from-teal-50 to-cyan-50 px-6 py-10 text-center sm:px-12 sm:py-14">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Ready to scope a pilot?</h2>
          <p className="mx-auto mt-3 max-w-lg leading-relaxed text-slate-600">
            Tell us your fleet, region, and AIS setup. We&apos;ll follow up with a short discovery call and a
            one-page SOW.
          </p>
          <Link
            className="mt-8 inline-flex items-center justify-center rounded-xl bg-teal-600 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-teal-600/20 transition hover:bg-teal-500"
            href="/contact"
          >
            Contact us
          </Link>
        </div>
      </section>
    </MarketingShell>
  );
}
