# AISTruth web (Next.js 14)

Next.js app: **landing** at [`/`](http://localhost:3000), **pilot program** at [`/pilot`](http://localhost:3000/pilot), **contact** at [`/contact`](http://localhost:3000/contact), and **dev console** at [`/console`](http://localhost:3000/console).

## Setup

```bash
cd frontend
npm install
```

Optional: point the browser at a non-default API:

```bash
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

**Contact form:** copy `.env.example` → `.env.local` and set `LEADS_SUBMIT_KEY` to match `AISTRUTH_LEADS_KEY` on the API. Enable leads on the API with `AISTRUTH_LEADS_ENABLED=true`. The form calls `POST /api/leads` (server-side proxy); it never hits the API directly from the browser.

Then open [http://localhost:3000](http://localhost:3000) or go straight to [http://localhost:3000/console](http://localhost:3000/console).

The FastAPI app must allow browser origins (defaults include `http://localhost:3000` via `AISTRUTH_CORS_ORIGINS` on the API).

## Requirements

- Node.js **18+** recommended (Next.js 14).

From the **repo root** you can also run `npm run dev` (delegates to `frontend`).
