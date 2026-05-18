import type { Metadata } from "next";

import Logo from "@/components/Logo";

export const metadata: Metadata = {
  title: "Console",
};

export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-900 bg-[radial-gradient(ellipse_100%_60%_at_50%_-15%,rgba(34,211,238,0.12),transparent_55%),radial-gradient(ellipse_70%_45%_at_100%_0%,rgba(59,130,246,0.08),transparent)]">
      <header className="sticky top-0 z-50 border-b border-slate-700/70 bg-slate-900/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3 sm:px-6">
          <Logo href="/" size="sm" />
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-cyan-300">
            Demo
          </span>
        </div>
      </header>
      {children}
    </div>
  );
}
