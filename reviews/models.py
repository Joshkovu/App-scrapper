import uuid

from django.conf import settings
from django.db import models


class TrackedApp(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tracked_apps")
    app_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    developer = models.CharField(max_length=500, blank=True)
    icon_url = models.URLField(max_length=2000, blank=True)
    store_url = models.URLField(max_length=2000)
    store_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    store_ratings = models.PositiveBigIntegerField(null=True, blank=True)
    last_scraped_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "app_id"], name="unique_user_app")]
        ordering = ["-last_scraped_at"]


class Review(models.Model):
    SENTIMENTS = [(value, value.title()) for value in ("positive", "negative", "neutral")]
    CATEGORIES = [(value, value) for value in ("UI/UX", "Bugs/Performance", "Pricing", "Feature Request", "General")]
    tracked_app = models.ForeignKey(TrackedApp, on_delete=models.CASCADE, related_name="reviews")
    review_id = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255, blank=True)
    rating = models.PositiveSmallIntegerField()
    content = models.TextField()
    thumbs_up = models.PositiveIntegerField(default=0)
    version = models.CharField(max_length=100, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    reply_content = models.TextField(blank=True)
    sentiment = models.CharField(max_length=20, choices=SENTIMENTS, default="neutral")
    category = models.CharField(max_length=40, choices=CATEGORIES, default="General")
    extracted_issue = models.TextField(blank=True)
    is_insightful = models.BooleanField(default=False)
    ai_processed = models.BooleanField(default=False)
    analyzed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tracked_app", "review_id"], name="unique_app_review")]
        ordering = ["-thumbs_up", "-published_at"]
