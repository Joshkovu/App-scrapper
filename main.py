from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google_play_scraper import Sort, app as fetch_app, reviews
from pydantic import BaseModel, Field, field_validator

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PACKAGE_ID_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)+$")

app = FastAPI(
    title="Play Review Lens",
    description="Live Google Play Store review analysis API",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ScrapeRequest(BaseModel):
    app_input: str = Field(..., min_length=1, max_length=2048)
    count: int = Field(default=300, ge=1, le=1000)
    lang: str = Field(default="en", min_length=2, max_length=8)
    country: str = Field(default="us", min_length=2, max_length=8)

    @field_validator("app_input")
    @classmethod
    def normalize_app_input(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter a Google Play URL or package ID.")
        return value

    @field_validator("lang", "country")
    @classmethod
    def normalize_locale(cls, value: str) -> str:
        return value.strip().lower()


class ReviewResponse(BaseModel):
    review_id: str
    user_name: str
    score: int
    content: str
    thumbs_up_count: int
    version: str | None = None
    published_at: str | None = None
    reply_content: str | None = None
    replied_at: str | None = None


def extract_package_id(app_input: str) -> str:
    candidate = app_input.strip()
    if PACKAGE_ID_PATTERN.fullmatch(candidate):
        return candidate

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in {
        "play.google.com",
        "www.play.google.com",
    }:
        raise ValueError("Use a package ID or a play.google.com app URL.")

    package_id = parse_qs(parsed.query).get("id", [""])[0]
    if not PACKAGE_ID_PATTERN.fullmatch(package_id):
        raise ValueError("The Play Store URL does not contain a valid app package ID.")
    return package_id


def serialize_timestamp(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    return timestamp.isoformat()


def process_reviews(raw_reviews: list[dict[str, Any]]) -> list[ReviewResponse]:
    if not raw_reviews:
        return []

    frame = pd.DataFrame(raw_reviews)
    frame["score"] = pd.to_numeric(frame.get("score"), errors="coerce").fillna(0).astype(int)
    frame["thumbsUpCount"] = pd.to_numeric(
        frame.get("thumbsUpCount"), errors="coerce"
    ).fillna(0).astype(int)
    frame["content"] = frame.get("content", pd.Series(dtype=str)).fillna("").astype(str)
    frame = frame.sort_values("at", ascending=False, na_position="last")

    result: list[ReviewResponse] = []
    for index, row in frame.iterrows():
        result.append(
            ReviewResponse(
                review_id=str(row.get("reviewId") or index),
                user_name=str(row.get("userName") or "Anonymous reviewer"),
                score=int(row["score"]),
                content=row["content"],
                thumbs_up_count=int(row["thumbsUpCount"]),
                version=str(row["reviewCreatedVersion"]) if pd.notna(row.get("reviewCreatedVersion")) else None,
                published_at=serialize_timestamp(row.get("at")),
                reply_content=(
                    str(row["replyContent"])
                    if pd.notna(row.get("replyContent"))
                    else None
                ),
                replied_at=serialize_timestamp(row.get("repliedAt")),
            )
        )
    return result


def build_summary(review_list: list[ReviewResponse]) -> dict[str, Any]:
    frame = pd.DataFrame([review.model_dump() for review in review_list])
    if frame.empty:
        return {
            "review_count": 0,
            "average_score": 0,
            "score_distribution": {str(score): 0 for score in range(1, 6)},
            "response_rate": 0,
        }

    distribution = frame["score"].value_counts().reindex(range(1, 6), fill_value=0)
    return {
        "review_count": int(len(frame)),
        "average_score": round(float(frame["score"].mean()), 2),
        "score_distribution": {str(score): int(distribution[score]) for score in range(1, 6)},
        "response_rate": round(float(frame["reply_content"].notna().mean() * 100), 1),
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scrape")
def scrape_reviews(request: ScrapeRequest) -> dict[str, Any]:
    try:
        package_id = extract_package_id(request.app_input)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        app_details = fetch_app(package_id, lang=request.lang, country=request.country)
        raw_reviews, _ = reviews(
            package_id,
            lang=request.lang,
            country=request.country,
            sort=Sort.NEWEST,
            count=request.count,
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Google Play Store could not be reached for {package_id}: {error}",
        ) from error

    review_list = process_reviews(raw_reviews[: request.count])
    return {
        "app": {
            "package_id": package_id,
            "title": app_details.get("title", package_id),
            "developer": app_details.get("developer", ""),
            "icon": app_details.get("icon", ""),
            "score": app_details.get("score"),
            "ratings": app_details.get("ratings"),
            "url": f"https://play.google.com/store/apps/details?id={package_id}",
        },
        "query": {
            "count_requested": request.count,
            "language": request.lang,
            "country": request.country,
        },
        "summary": build_summary(review_list),
        "reviews": [review.model_dump() for review in review_list],
    }


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
