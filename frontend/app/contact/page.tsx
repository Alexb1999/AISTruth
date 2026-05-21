import type { Metadata } from "next";
import Link from "next/link";

import ContactForm from "@/components/ContactForm";
import MarketingShell from "@/components/MarketingShell";

export const metadata: Metadata = {
  title: "Contact",
  description: "Request an AISTruth pilot or ask about enterprise AIS integrity validation.",
};

export default function ContactPage() {
  return (
    <MarketingShell active="contact">
      <section className="border-b border-slate-200/80 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
          <p className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-teal-700">
            Get in touch
          </p>
          <h1 className="mt-4 max-w-2xl text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Request a pilot or ask a question.
          </h1>
          <p className="mt-4 max-w-xl text-lg leading-relaxed text-slate-600">
            We typically respond within two business days with next steps — a demo walkthrough, discovery call, or
            draft pilot scope.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(300px,420px)] lg:items-start lg:gap-14">
          <div className="space-y-8">
            <dl className="grid gap-6 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <dt className="text-sm font-semibold text-slate-900">Best for</dt>
                <dd className="mt-2 text-sm leading-relaxed text-slate-600">
                  Fleet operators, charter desks, port and coastal authorities, and compliance teams evaluating AIS
                  integrity evidence — including regional monitoring of all vessels in an area.
                </dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <dt className="text-sm font-semibold text-slate-900">Before you write</dt>
                <dd className="mt-2 text-sm leading-relaxed text-slate-600">
                  Try the{" "}
                  <Link className="font-medium text-teal-700 hover:underline" href="/console">
                    demo console
                  </Link>{" "}
                  or read the{" "}
                  <Link className="font-medium text-teal-700 hover:underline" href="/pilot">
                    pilot program
                  </Link>
                  .
                </dd>
              </div>
            </dl>
          </div>

          <ContactForm />
        </div>
      </section>
    </MarketingShell>
  );
}
