"use client";

import { outcomeHeadline, outcomeTier, tierPresentation } from "@/lib/validationOutcome";
import type { ValidateResponse } from "@/lib/types";

export default function ValidationOutcomeCard({ data }: { data: ValidateResponse }) {
  const tier = outcomeTier(data);
  const pres = tierPresentation[tier];
  const headline = outcomeHeadline(data);

  return (
    <div
      className={`rounded-2xl border bg-slate-800/90 px-5 py-4 shadow-md ring-1 ring-white/[0.05] ${pres.borderClass}`}
      role="region"
      aria-label="Validation outcome summary"
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <span
          className={`inline-flex items-center rounded-md px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ring-1 ${pres.badgeClass}`}
        >
          {pres.label}
        </span>
      </div>
      <p className="mt-3 text-[15px] leading-relaxed text-slate-100">{headline}</p>
    </div>
  );
}
