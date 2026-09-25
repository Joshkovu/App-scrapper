# Signal / App Review Intelligence

Authenticated Django REST + React dashboard for live Google Play review analysis. Reviews are collected with `google-play-scraper`, ranked and filtered with pandas, analyzed in real batches by Gemini 2.5 Flash, and persisted in PostgreSQL.

## Local development

Backend (SQLite fallback is used when `DATABASE_URL` is unset):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
$env:GEMINI_API_KEY = "your-google-ai-studio-key"
python manage.py runserver 8000
```

Frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. A Gemini API key is required for `/api/apps/scrape/`; the app deliberately fails clearly rather than returning mock analysis.

## Render (API)

Deploy the backend with the **Python 3** native runtime from `render.yaml`, not Docker.

1. In the Render dashboard, open **app-scrapper-api** → **Settings** → **Build & Deploy**.
2. Set **Environment** to **Python 3** (not Docker). There is no `Dockerfile` at the repo root on purpose.
3. **Sync** or apply the Blueprint so `buildCommand` and `startCommand` match `render.yaml`.
4. Redeploy. Builds use Render’s Python pipeline instead of Docker BuildKit pushing to `image-registry-v2…internal.render.com`.

If a deploy log shows `#10 RUN pip install` / `exporting to image` / `failed to push image-registry-v2`, the service is still on Docker—switch to Python 3 and redeploy. Transient `connection refused` on the internal registry can also be cleared with **Clear build cache** and retry; contact Render support if it persists.

Required env vars: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY` (see `render.yaml`).

## Docker Compose

Set `GEMINI_API_KEY` in the shell, then run:

```powershell
docker compose up --build
```

The React app is at http://localhost:5173 and the Django API is at http://localhost:8000.

## Cloudflare Pages

In the Pages project settings use:

- Root directory: `frontend`
- Build command: `npm run build`
- Build output directory: `dist`
- Deploy command: leave it empty; Pages performs the deployment itself

For a manual deployment from `frontend`, run:

```powershell
npm run deploy:pages
```

Do not use `wrangler deploy` for this project. That is the Workers command and expects a Worker entry point or an `[assets]` configuration. This project is a static Vite SPA and uses `wrangler pages deploy`.

## API

- `POST /api/auth/signup/` with `{ "email", "password" }`
- `POST /api/auth/login/` with `{ "email", "password" }`
- `POST /api/apps/scrape/` with `{ "app_input", "count": 300, "lang": "en", "country": "us" }`
- `GET /api/apps/`
- `GET /api/apps/<uuid>/reviews/?sentiment=negative&category=Bugs/Performance`

All app endpoints require `Authorization: Bearer <access-token>`.
