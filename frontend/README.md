# DDI Frontend (minimal)

This is a minimal Vite + React + TypeScript frontend that calls the backend API.

Setup:

```bash
cd frontend
npm install
npm run dev
```

Environment:
- `VITE_API_BASE_URL` — base URL for the backend with API prefix (default `http://localhost:8000/api/v1`)

Notes:
- This scaffold includes `src/api/*` modules that call the backend endpoints.
- `App.tsx` is wired to the backend POST `/analyze` endpoint and renders real DDI analysis results.
- Once analysis completes, the app can export a downloadable PDF report using the `/api/v1/export-report` endpoint.
