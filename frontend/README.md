# AISTruth web (Next.js 14)

Next.js app: **landing** at [`/`](http://localhost:3000) and **dev console** at [`/console`](http://localhost:3000/console) for calling FastAPI **`/v1/validate/{mmsi}`**.

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

Then open [http://localhost:3000](http://localhost:3000) or go straight to [http://localhost:3000/console](http://localhost:3000/console).

The FastAPI app must allow browser origins (defaults include `http://localhost:3000` via `AISTRUTH_CORS_ORIGINS` on the API).

## Requirements

- Node.js **18+** recommended (Next.js 14).

From the **repo root** you can also run `npm run dev` (delegates to `frontend`).
