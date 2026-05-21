import Link from "next/link";
import dynamic from "next/dynamic";

import MarketingShell from "@/components/MarketingShell";

const LandingMapDemo = dynamic(() => import("@/components/LandingMapDemo"), { ssr: false });

const CAPABILITIES = [
  {
    title: "Explainable integrity scores",
    description:
      "Motion heuristics and spoofing checks roll up into a score your ops and compliance teams can defend — not a black-box ML guess.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    accent: "text-teal-600 bg-teal-50 ring-teal-100",
  },
  {
    title: "GEODNET reference context",
    description:
      "Nearest-station baseline and optional NTRIP telemetry show whether correction infrastructure is reachable where the vessel reports — without claiming rover-class fixes.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
      </svg>
    ),
    accent: "text-sky-600 bg-sky-50 ring-sky-100",
  },
  {
    title: "Map-first evidence",
    description:
      "AIS track, reference stations, and correction sampling on one map — built for briefings with masters, charterers, and port authorities.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934a1.125 1.125 0 01-1.044 0l-3.869-1.934A1.125 1.125 0 0012 3.75v16.5" />
      </svg>
    ),
    accent: "text-indigo-600 bg-indigo-50 ring-indigo-100",
  },
];

const USE_CASES = [
  {
    role: "Fleet operations",
    text: "Flag inconsistent tracks before port entry, bunkering, or ship-to-ship transfers.",
  },
  {
    role: "Chartering & trade",
    text: "Add an independent integrity readout alongside AIS for voyage performance and dispute prep.",
  },
  {
    role: "Coastal monitoring",
    text: "Screen Norwegian coastal traffic with live feeds, reference geometry, and plain-language findings.",
  },
];

const STEPS = [
  { n: "01", title: "Ingest AIS", text: "Pull historic or live positions for any MMSI in your permitted feed." },
  { n: "02", title: "Run checks", text: "Motion, spoofing heuristics, and GEODNET baseline in one API call." },
  { n: "03", title: "Act on evidence", text: "Share the score, map, and flags — or pipe JSON into your own systems." },
];

export default function LandingPage() {
  return (
    <MarketingShell active="product">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-200/80 bg-white">
        <div
          className="pointer-events-none absolute -right-32 -top-32 h-[28rem] w-[28rem] rounded-full bg-gradient-to-br from-cyan-200/50 to-teal-100/30 blur-3xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -bottom-24 -left-24 h-80 w-80 rounded-full bg-gradient-to-tr from-sky-100/60 to-transparent blur-3xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_0%,#000_50%,transparent_100%)] opacity-40"
          aria-hidden
        />

        <div className="relative mx-auto grid max-w-6xl gap-10 px-5 pb-16 pt-8 sm:px-6 lg:grid-cols-2 lg:items-center lg:gap-12 lg:pb-20 lg:pt-10">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-700">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
              Maritime AIS integrity
            </p>
            <h1 className="mt-5 text-4xl font-semibold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl lg:text-[3.25rem]">
              Know when to trust a vessel&apos;s reported position.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-slate-600">
              AISTruth validates AIS tracks against motion heuristics, spoofing signals, and GEODNET reference
              geometry — so shipping teams get an explainable integrity readout, not another opaque dashboard.
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
                Try the live demo
              </Link>
            </div>
            <dl className="mt-10 grid grid-cols-3 gap-4 border-t border-slate-200 pt-8">
              <div>
                <dt className="text-2xl font-semibold tabular-nums text-slate-900">24h</dt>
                <dd className="mt-0.5 text-xs text-slate-500">AIS track window</dd>
              </div>
              <div>
                <dt className="text-2xl font-semibold tabular-nums text-slate-900">API</dt>
                <dd className="mt-0.5 text-xs text-slate-500">Integrate or use console</dd>
              </div>
              <div>
                <dt className="text-2xl font-semibold tabular-nums text-slate-900">Plain</dt>
                <dd className="mt-0.5 text-xs text-slate-500">Language findings</dd>
              </div>
            </dl>
          </div>

          {/* Live map preview */}
          <div className="relative z-0 isolate lg:justify-self-end">
            <div className="landing-map rounded-2xl border border-slate-200 bg-white p-1.5 shadow-2xl shadow-slate-300/40 ring-1 ring-slate-100">
              <LandingMapDemo />
            </div>
            <p className="mt-3 text-center text-xs text-slate-500">
              Example validation — AIS track, GEODNET correction zones, and refined leg overlay
            </p>
          </div>
        </div>
      </section>

      {/* Capabilities */}
      <section id="capabilities" className="mx-auto max-w-6xl px-5 py-20 sm:px-6">
        <div className="max-w-2xl">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            Built for teams who answer &ldquo;can we trust this AIS?&rdquo;
          </h2>
          <p className="mt-3 text-slate-600 leading-relaxed">
            Spoofing, stale feeds, and impossible motion erode confidence in vessel reporting. AISTruth gives operators
            and charter desks a structured answer — with evidence they can show, not just a red/green light.
          </p>
        </div>
        <ul className="mt-12 grid gap-6 md:grid-cols-3">
          {CAPABILITIES.map((item) => (
            <li
              key={item.title}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-slate-300 hover:shadow-md"
            >
              <span className={`inline-flex rounded-lg p-2.5 ring-1 ${item.accent}`}>{item.icon}</span>
              <h3 className="mt-4 text-base font-semibold text-slate-900">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{item.description}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:px-6">
          <h2 className="text-center text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">How it works</h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
            One MMSI in, integrity evidence out — via REST API or the interactive console.
          </p>
          <ol className="mt-14 grid gap-8 md:grid-cols-3">
            {STEPS.map((step) => (
              <li key={step.n} className="relative text-center md:text-left">
                <span className="text-3xl font-bold tabular-nums text-teal-200">{step.n}</span>
                <h3 className="mt-2 text-lg font-semibold text-slate-900">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{step.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Use cases */}
      <section className="mx-auto max-w-6xl px-5 py-20 sm:px-6">
        <div className="rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 px-6 py-10 text-white sm:px-10 sm:py-12">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Where shipping teams use it</h2>
          <p className="mt-3 max-w-2xl text-slate-300 leading-relaxed">
            Early pilots focus on coastal Norway — the architecture is feed-agnostic for operators with permitted AIS
            access elsewhere.
          </p>
          <ul className="mt-10 grid gap-6 sm:grid-cols-3">
            {USE_CASES.map((item) => (
              <li key={item.role} className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm">
                <h3 className="text-sm font-semibold text-teal-300">{item.role}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">{item.text}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-5 pb-20 pt-4 sm:px-6">
        <div className="rounded-2xl border border-teal-200 bg-gradient-to-br from-teal-50 to-cyan-50 px-6 py-10 text-center sm:px-12 sm:py-14">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            See it on a real vessel track
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-slate-600 leading-relaxed">
            Open the demo console or tell us about your fleet — we&apos;ll scope a pilot with your AIS feed and
            operating area.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              className="inline-flex items-center justify-center rounded-xl bg-teal-600 px-7 py-3.5 text-sm font-semibold text-white shadow-lg shadow-teal-600/20 transition hover:bg-teal-500"
              href="/contact"
            >
              Request pilot
            </Link>
            <Link
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-7 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              href="/console"
            >
              Launch demo console
            </Link>
          </div>
        </div>
      </section>
    </MarketingShell>
  );
}
