# AISTruth web (Next.js 14)

Minimal dev UI for calling the FastAPI **`/v1/validate/{mmsi}`** endpoint.

## Setup

```bash
cd apps/web
npm install
```

Optional: point the browser at a non-default API:

```bash
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

The FastAPI app must allow browser origins (defaults include `http://localhost:3000` via `AISTRUTH_CORS_ORIGINS` on the API).

## Requirements

- Node.js **18+** recommended (Next.js 14).
