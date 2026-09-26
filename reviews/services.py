from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from google_play_scraper import Sort, app as fetch_app, reviews as fetch_reviews

from .models import Review, TrackedApp

logger = logging.getLogger(__name__)
PACKAGE_ID_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)+$")
ALLOWED_SENTIMENTS = {"positive", "negative", "neutral"}
ALLOWED_CATEGORIES = {"UI/UX", "Bugs/Performance", "Pricing", "Feature Request", "General"}


def extract_package_id(app_input: str) -> str:
    candidate = app_input.strip()
    if PACKAGE_ID_PATTERN.fullmatch(candidate):
        return candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in {"play.google.com", "www.play.google.com"}:
        raise ValueError("Use a Google Play package ID or a play.google.com app URL.")
    package_id = parse_qs(parsed.query).get("id", [""])[0]
    if not PACKAGE_ID_PATTERN.fullmatch(package_id):
        raise ValueError("The Play Store URL does not contain a valid package ID.")
    return package_id


def _timestamp(value: Any) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    return parsed.to_pydatetime()


def classify_by_keywords(content: str) -> str:
    rules = (
        ("Bugs/Performance", r"\b(crash|bug|freez\w*|glitch|error|lag)\b"),
        ("UI/UX", r"\b(ui|layout|design|button|screen|color)\b"),
        ("Pricing", r"\b(price|subscription|cost|pay|expensive|refund)\b"),
    )
    for category, pattern in rules:
        if re.search(pattern, content, re.IGNORECASE):
            return category
    return "General"


def _normalize_reviews(raw_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not raw_reviews:
        return []
    frame = pd.DataFrame(raw_reviews)
    frame["content"] = frame.get("content", pd.Series(dtype=str)).fillna("").astype(str)
    frame["thumbsUpCount"] = pd.to_numeric(frame.get("thumbsUpCount"), errors="coerce").fillna(0).astype(int)
    frame = frame.sort_values(["thumbsUpCount", "at"], ascending=[False, False], na_position="last")
    return frame.to_dict("records")


def _gemini_extract(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not settings.GEMINI_API_KEY:
        return []
    from google import genai

    payload = [{"review_id": str(item.get("reviewId", "")), "score": item.get("score"), "content": item.get("content", "")} for item in batch]
    prompt = """Analyze these Google Play reviews. Return ONLY a valid JSON array, with one object per review, using exactly these keys: review_id, sentiment, category, extracted_issue, is_insightful. sentiment must be positive, negative, or neutral. category must be UI/UX, Bugs/Performance, Pricing, Feature Request, or General. extracted_issue must be one plain-text sentence describing the specific thing that worked or broke. Mark vague, empty, or non-actionable reviews is_insightful false. Preserve every review_id exactly. Reviews:\n""" + json.dumps(payload, ensure_ascii=False)
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.1},
            )
            parsed = json.loads(response.text)
            if not isinstance(parsed, list):
                raise ValueError("Gemini returned a non-array response.")
            return parsed
        except Exception as error:
            if attempt == 2 or "429" not in str(error):
                raise RuntimeError(f"Gemini extraction failed: {error}") from error
            time.sleep(2**attempt)
    return []


def _analyze(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    analyzed: dict[str, dict[str, Any]] = {}
    for start in range(0, len(candidates), 25):
        for item in _gemini_extract(candidates[start:start + 25]):
            review_id = str(item.get("review_id", ""))
            if review_id:
                analyzed[review_id] = {
                    "sentiment": item.get("sentiment") if item.get("sentiment") in ALLOWED_SENTIMENTS else "neutral",
                    "category": item.get("category") if item.get("category") in ALLOWED_CATEGORIES else "General",
                    "extracted_issue": str(item.get("extracted_issue", ""))[:2000],
                    "is_insightful": bool(item.get("is_insightful", False)),
                }
    return analyzed


@transaction.atomic
def _persist_scraped_reviews(*, user, package_id: str, metadata: dict[str, Any], reviews: list[dict[str, Any]]) -> tuple[TrackedApp, list[Review]]:
    tracked_app, _ = TrackedApp.objects.update_or_create(
        user=user,
        app_id=package_id,
        defaults={
            "title": metadata.get("title", package_id),
            "developer": metadata.get("developer", ""),
            "icon_url": metadata.get("icon", ""),
            "store_url": f"https://play.google.com/store/apps/details?id={package_id}",
            "store_score": metadata.get("score"),
            "store_ratings": metadata.get("ratings"),
        },
    )
    saved_reviews: list[Review] = []
    for item in reviews:
        review_id = str(item.get("reviewId", ""))
        if not review_id:
            continue
        content = str(item.get("content", ""))
        score = max(1, min(5, int(item.get("score") or 1)))
        thumbs_up = max(0, int(item.get("thumbsUpCount") or 0))
        review, _ = Review.objects.update_or_create(
            tracked_app=tracked_app,
            review_id=review_id,
            defaults={
                "user_name": str(item.get("userName", "Anonymous reviewer")),
                "rating": score,
                "content": content,
                "thumbs_up": thumbs_up,
                "version": str(item.get("reviewCreatedVersion") or ""),
                "published_at": _timestamp(item.get("at")),
                "reply_content": str(item.get("replyContent") or ""),
                "sentiment": "positive" if score >= 4 else "negative" if score <= 2 else "neutral",
                "category": classify_by_keywords(content),
                "extracted_issue": "",
                "is_insightful": thumbs_up > 0 and len(content) > 25,
                "ai_processed": False,
                "analyzed_at": None,
            },
        )
        saved_reviews.append(review)
    return tracked_app, saved_reviews


def _enrich_with_gemini(review_objects: list[Review]) -> None:
    candidates = [review for review in review_objects if review.is_insightful and not review.ai_processed][:30]
    if not candidates:
        return
    analysis = _analyze([{"reviewId": str(review.id), "score": review.rating, "content": review.content} for review in candidates])
    for review in candidates:
        insight = analysis.get(str(review.id))
        if not insight:
            continue
        Review.objects.filter(id=review.id).update(
            sentiment=insight["sentiment"],
            category=insight["category"],
            extracted_issue=insight["extracted_issue"],
            ai_processed=True,
            analyzed_at=timezone.now(),
        )


def scrape_and_persist(*, user, app_input: str, lang: str = "en", country: str = "us", count: int = 300) -> TrackedApp:
    package_id = extract_package_id(app_input)
    metadata = fetch_app(package_id, lang=lang, country=country)
    raw_reviews, _ = fetch_reviews(package_id, lang=lang, country=country, sort=Sort.MOST_RELEVANT, count=min(count, 1000))
    normalized_reviews = _normalize_reviews(raw_reviews[:count])
    tracked_app, saved_reviews = _persist_scraped_reviews(
        user=user,
        package_id=package_id,
        metadata=metadata,
        reviews=normalized_reviews,
    )
    try:
        _enrich_with_gemini(saved_reviews)
    except Exception as error:
        logger.warning("AI enrichment bypassed after raw reviews were saved: %s", error, exc_info=True)
    return tracked_app
