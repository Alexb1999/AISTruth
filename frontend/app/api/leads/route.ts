import { NextResponse } from "next/server";

const API_BASE = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const leadsKey = process.env.LEADS_SUBMIT_KEY;
  if (!leadsKey) {
    return NextResponse.json(
      { detail: "Contact form is not configured on this deployment." },
      { status: 503 },
    );
  }

  let body: string;
  try {
    body = await request.text();
  } catch {
    return NextResponse.json({ detail: "Invalid request body." }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${API_BASE}/v1/leads`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Leads-Key": leadsKey,
      },
      body,
      cache: "no-store",
    });

    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
    });
  } catch {
    return NextResponse.json({ detail: "Could not reach the API server." }, { status: 502 });
  }
}
