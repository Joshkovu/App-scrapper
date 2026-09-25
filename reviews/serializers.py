from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Review, TrackedApp

User = get_user_model()


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def create(self, validated_data):
        email = validated_data["email"].lower()
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError({"email": "An account with this email already exists."})
        return User.objects.create_user(username=email, email=email, password=validated_data["password"])


class ReviewSerializer(serializers.ModelSerializer):
    score = serializers.IntegerField(source="rating", read_only=True)
    thumbs_up_count = serializers.IntegerField(source="thumbs_up", read_only=True)

    class Meta:
        model = Review
        fields = ["review_id", "user_name", "rating", "score", "content", "thumbs_up", "thumbs_up_count", "version", "published_at", "reply_content", "sentiment", "category", "extracted_issue", "is_insightful", "ai_processed"]


class TrackedAppSerializer(serializers.ModelSerializer):
    review_count = serializers.SerializerMethodField()
    package_id = serializers.CharField(source="app_id", read_only=True)

    def get_review_count(self, obj):
        return getattr(obj, "review_count", obj.reviews.count())

    class Meta:
        model = TrackedApp
        fields = ["id", "app_id", "package_id", "title", "developer", "icon_url", "store_url", "store_score", "store_ratings", "review_count", "last_scraped_at"]
