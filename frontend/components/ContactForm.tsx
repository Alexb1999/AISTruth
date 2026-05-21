"use client";

import { useState } from "react";

const REGIONS = [
  "Norwegian coastal waters",
  "Canada — Atlantic",
  "Canada — Pacific / Arctic",
  "Europe (other)",
  "Other / global",
] as const;

const MONITORING_SCOPES = [
  "Port or coastal authority — all vessels in vicinity",
  "Regional / area monitoring (no owned fleet)",
  "Fleet operator — 1–5 vessels",
  "Fleet operator — 6–25 vessels",
  "Fleet operator — 26–100 vessels",
  "Fleet operator — 100+ vessels",
  "Not sure yet",
] as const;

const AIS_FEEDS = [
  "BarentsWatch / Norway open AIS",
  "Spire Maritime (BYOK)",
  "Other licensed AIS feed",
  "No feed yet — need guidance",
] as const;

type FormState = {
  name: string;
  organization: string;
  email: string;
  region: string;
  fleet_size: string;
  ais_feed: string;
  message: string;
  website: string;
};

const INITIAL: FormState = {
  name: "",
  organization: "",
  email: "",
  region: REGIONS[0],
  fleet_size: "",
  ais_feed: AIS_FEEDS[0],
  message: "",
  website: "",
};

export default function ContactForm() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name.trim(),
          organization: form.organization.trim(),
          email: form.email.trim(),
          region: form.region,
          fleet_size: form.fleet_size,
          ais_feed: form.ais_feed,
          message: form.message.trim() || null,
          website: form.website,
        }),
      });
      const text = await res.text();
      if (!res.ok) {
        let detail = text.trim() || `Request failed (${res.status})`;
        try {
          const j = JSON.parse(text) as { detail?: unknown };
          if (typeof j.detail === "string") detail = j.detail;
        } catch {
          /* keep raw */
        }
        throw new Error(detail);
      }
      setSuccess(true);
      setForm(INITIAL);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="rounded-2xl border border-teal-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-100 text-teal-700">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="mt-4 text-lg font-semibold text-slate-900">Thanks — we received your request.</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          We&apos;ll follow up by email shortly. In the meantime you can explore the{" "}
          <a className="font-medium text-teal-700 hover:underline" href="/console">
            demo console
          </a>
          .
        </p>
        <button
          className="mt-6 text-sm font-medium text-teal-700 hover:underline"
          type="button"
          onClick={() => setSuccess(false)}
        >
          Submit another inquiry
        </button>
      </div>
    );
  }

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20";
  const labelClass = "text-sm font-medium text-slate-700";

  return (
    <form
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
      onSubmit={(e) => void submit(e)}
    >
      <h2 className="text-lg font-semibold text-slate-900">Pilot inquiry</h2>
      <p className="mt-1 text-sm text-slate-500">Fields marked * are required.</p>

      <div className="mt-6 grid gap-4">
        <label className="grid gap-1.5">
          <span className={labelClass}>Name *</span>
          <input
            className={inputClass}
            required
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            autoComplete="name"
          />
        </label>

        <label className="grid gap-1.5">
          <span className={labelClass}>Organization *</span>
          <input
            className={inputClass}
            required
            value={form.organization}
            onChange={(e) => update("organization", e.target.value)}
            autoComplete="organization"
          />
        </label>

        <label className="grid gap-1.5">
          <span className={labelClass}>Work email *</span>
          <input
            className={inputClass}
            type="email"
            required
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            autoComplete="email"
          />
        </label>

        <label className="grid gap-1.5">
          <span className={labelClass}>Operating region *</span>
          <select
            className={inputClass}
            value={form.region}
            onChange={(e) => update("region", e.target.value)}
          >
            {REGIONS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1.5">
          <span className={labelClass}>Monitoring scope *</span>
          <select
            className={inputClass}
            required
            value={form.fleet_size}
            onChange={(e) => update("fleet_size", e.target.value)}
          >
            <option value="" disabled>
              Select scope…
            </option>
            {MONITORING_SCOPES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <span className="text-xs text-slate-500">
            Ports and authorities: choose the regional option if you monitor traffic in an area, not a owned fleet.
          </span>
        </label>

        <label className="grid gap-1.5">
          <span className={labelClass}>AIS data source</span>
          <select
            className={inputClass}
            value={form.ais_feed}
            onChange={(e) => update("ais_feed", e.target.value)}
          >
            {AIS_FEEDS.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-1.5">
          <span className={labelClass}>Message</span>
          <textarea
            className={`${inputClass} min-h-[6rem] resize-y`}
            value={form.message}
            onChange={(e) => update("message", e.target.value)}
            placeholder="MMSIs, use case, timeline, or questions…"
          />
        </label>

        {/* Honeypot — hidden from users */}
        <label className="hidden" aria-hidden tabIndex={-1}>
          Website
          <input
            tabIndex={-1}
            autoComplete="off"
            value={form.website}
            onChange={(e) => update("website", e.target.value)}
          />
        </label>
      </div>

      {error ? (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-800">
          {error}
        </p>
      ) : null}

      <button
        className="mt-6 w-full rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-teal-600/20 transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-60"
        disabled={loading}
        type="submit"
      >
        {loading ? "Sending…" : "Submit inquiry"}
      </button>
    </form>
  );
}
