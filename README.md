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

## Docker Compose

Set `GEMINI_API_KEY` in the shell, then run:

```powershell
docker compose up --build
```

The React app is at http://localhost:5173 and the Django API is at http://localhost:8000.

## API

- `POST /api/auth/signup/` with `{ "email", "password" }`
- `POST /api/auth/login/` with `{ "email", "password" }`
- `POST /api/apps/scrape/` with `{ "app_input", "count": 300, "lang": "en", "country": "us" }`
- `GET /api/apps/`
- `GET /api/apps/<uuid>/reviews/?sentiment=negative&category=Bugs/Performance`

All app endpoints require `Authorization: Bearer <access-token>`.
