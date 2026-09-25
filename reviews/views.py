from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review, TrackedApp
from .serializers import ReviewSerializer, TrackedAppSerializer
from .services import scrape_and_persist


class ScrapeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        app_input = str(request.data.get("app_input", "")).strip()
        try:
            count = int(request.data.get("count", 300))
        except (TypeError, ValueError):
            return Response({"detail": "count must be an integer between 1 and 300."}, status=status.HTTP_400_BAD_REQUEST)
        if not app_input:
            return Response({"detail": "app_input is required."}, status=status.HTTP_400_BAD_REQUEST)
        if count < 1 or count > 300:
            return Response({"detail": "count must be between 1 and 300."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            tracked_app = scrape_and_persist(
                user=request.user,
                app_input=app_input,
                lang=str(request.data.get("lang", "en")).lower(),
                country=str(request.data.get("country", "us")).lower(),
                count=count,
            )
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as error:
            return Response({"detail": str(error)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(TrackedAppSerializer(tracked_app).data, status=status.HTTP_200_OK)


class AppListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrackedAppSerializer

    def get_queryset(self):
        return TrackedApp.objects.filter(user=self.request.user).annotate(review_count=Count("reviews"))


class ReviewListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        app = get_object_or_404(TrackedApp, id=self.kwargs["app_id"], user=self.request.user)
        queryset = Review.objects.filter(tracked_app=app)
        sentiment = self.request.query_params.get("sentiment")
        category = self.request.query_params.get("category")
        if sentiment:
            queryset = queryset.filter(sentiment=sentiment)
        if category:
            queryset = queryset.filter(category=category)
        return queryset
