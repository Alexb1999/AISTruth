export default function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-600/60 bg-slate-800/60 px-4 py-3 ring-1 ring-white/[0.04]">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold tabular-nums text-white" title={value}>
        {value}
      </p>
      {hint ? <p className="mt-0.5 truncate text-[11px] text-slate-500">{hint}</p> : null}
    </div>
  );
}
