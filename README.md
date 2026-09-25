# Play Review Lens

A production-ready FastAPI dashboard that fetches live Google Play Store reviews with `google-play-scraper`, processes the result with pandas, and presents a searchable review workspace.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000.

## Docker

```powershell
docker build -t play-review-lens .
docker run --rm -p 8000:8000 play-review-lens
```

## API

`POST /api/scrape` accepts a Play Store URL or package ID:

```json
{
  "app_input": "com.spotify.music",
  "count": 300,
  "lang": "en",
  "country": "us"
}
```

`count` is limited to 1-1000. The endpoint returns live app metadata, score distribution, response rate, and normalized review records. Invalid input returns `422`; upstream Play Store failures return `502`.
