import Link from "next/link";
import type { ReactNode } from "react";

import Logo from "@/components/Logo";

type NavKey = "product" | "pilot" | "contact" | "demo";

type MarketingShellProps = {
  children: ReactNode;
  active?: NavKey;
};

const NAV: { key: NavKey; label: string; href: string }[] = [
  { key: "product", label: "Product", href: "/#capabilities" },
  { key: "pilot", label: "Pilot", href: "/pilot" },
  { key: "contact", label: "Contact", href: "/contact" },
];

function navLinkClass(active: boolean): string {
  return active
    ? "text-slate-900"
    : "text-slate-600 transition-colors hover:text-slate-900";
}

export default function MarketingShell({ children, active }: MarketingShellProps) {
  return (
    <div className="marketing-page min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-[1000] border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:h-16 sm:px-6">
          <Logo href="/" size="nav" priority />

          <nav className="hidden items-center gap-6 text-sm font-medium md:flex" aria-label="Main">
            {NAV.map((item) => (
              <Link key={item.key} className={navLinkClass(active === item.key)} href={item.href}>
                {item.label}
              </Link>
            ))}
            <a
              className="text-slate-600 transition-colors hover:text-slate-900"
              href="https://github.com/Alexb1999/AISTruth"
              rel="noreferrer"
              target="_blank"
            >
              GitHub
            </a>
          </nav>

          <div className="flex shrink-0 items-center gap-2">
            <Link
              className="hidden rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 sm:inline-flex"
              href="/console"
            >
              Demo
            </Link>
            <Link
              className="rounded-lg bg-teal-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-sm shadow-teal-600/20 transition hover:bg-teal-500 sm:px-4 sm:py-2"
              href="/contact"
            >
              Request pilot
            </Link>
          </div>
        </div>

        <nav
          className="flex gap-5 overflow-x-auto border-t border-slate-100 px-4 py-2.5 text-sm font-medium md:hidden"
          aria-label="Main mobile"
        >
          {NAV.map((item) => (
            <Link key={item.key} className={`shrink-0 ${navLinkClass(active === item.key)}`} href={item.href}>
              {item.label}
            </Link>
          ))}
          <Link className="shrink-0 text-slate-600" href="/console">
            Demo
          </Link>
        </nav>
      </header>

      <main>{children}</main>

      <footer className="border-t border-slate-200 bg-white py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-4 sm:flex-row sm:px-6">
          <Logo href="/" size="sm" />
          <p className="max-w-sm text-center text-xs leading-relaxed text-slate-500 sm:text-right">
            Pilot partnerships &amp; enterprise integrations — open source core, commercial pilots welcome.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-slate-500">
            <Link className="transition hover:text-slate-700" href="/pilot">
              Pilot program
            </Link>
            <Link className="transition hover:text-slate-700" href="/contact">
              Contact
            </Link>
            <Link className="transition hover:text-slate-700" href="/console">
              Demo console
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
