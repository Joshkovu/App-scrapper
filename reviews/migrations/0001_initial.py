import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(
            name="TrackedApp",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("package_id", models.CharField(max_length=255)),
                ("title", models.CharField(max_length=500)),
                ("developer", models.CharField(blank=True, max_length=500)),
                ("icon_url", models.URLField(blank=True, max_length=2000)),
                ("store_url", models.URLField(max_length=2000)),
                ("store_score", models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True)),
                ("store_ratings", models.PositiveBigIntegerField(blank=True, null=True)),
                ("last_scraped_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tracked_apps", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-last_scraped_at"]},
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("review_id", models.CharField(max_length=255)),
                ("user_name", models.CharField(blank=True, max_length=255)),
                ("score", models.PositiveSmallIntegerField()),
                ("content", models.TextField()),
                ("thumbs_up_count", models.PositiveIntegerField(default=0)),
                ("version", models.CharField(blank=True, max_length=100)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("reply_content", models.TextField(blank=True)),
                ("sentiment", models.CharField(choices=[("positive", "Positive"), ("negative", "Negative"), ("neutral", "Neutral")], default="neutral", max_length=20)),
                ("category", models.CharField(choices=[("UI/UX", "UI/UX"), ("Bugs/Performance", "Bugs/Performance"), ("Pricing", "Pricing"), ("Feature Request", "Feature Request"), ("General", "General")], default="General", max_length=40)),
                ("extracted_issue", models.TextField(blank=True)),
                ("is_insightful", models.BooleanField(default=False)),
                ("analyzed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tracked_app", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="reviews.trackedapp")),
            ],
            options={"ordering": ["-thumbs_up_count", "-published_at"]},
        ),
        migrations.AddConstraint(model_name="trackedapp", constraint=models.UniqueConstraint(fields=("owner", "package_id"), name="unique_owner_package")),
        migrations.AddConstraint(model_name="review", constraint=models.UniqueConstraint(fields=("tracked_app", "review_id"), name="unique_app_review")),
    ]
