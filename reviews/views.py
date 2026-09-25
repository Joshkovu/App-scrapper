from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exports import build_excel_export, build_pdf_export, export_filename
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


def _filtered_reviews(request, app):
    queryset = Review.objects.filter(tracked_app=app)
    sentiment = request.query_params.get("sentiment")
    category = request.query_params.get("category")
    search = request.query_params.get("search", "").strip()
    if sentiment:
        queryset = queryset.filter(sentiment=sentiment)
    if category:
        queryset = queryset.filter(category=category)
    if search:
        queryset = queryset.filter(
            Q(content__icontains=search)
            | Q(user_name__icontains=search)
            | Q(extracted_issue__icontains=search)
            | Q(category__icontains=search)
        )
    return queryset


class ReviewListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewSerializer

    def get_queryset(self):
        app = get_object_or_404(TrackedApp, id=self.kwargs["app_id"], user=self.request.user)
        return _filtered_reviews(self.request, app)


class ReviewExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, app_id):
        app = get_object_or_404(TrackedApp, id=app_id, user=request.user)
        export_format = request.query_params.get("format", "xlsx").lower()
        if export_format not in {"xlsx", "pdf"}:
            return Response({"detail": "format must be xlsx or pdf."}, status=status.HTTP_400_BAD_REQUEST)

        reviews = list(_filtered_reviews(request, app))
        if export_format == "pdf":
            payload = build_pdf_export(app, reviews)
            content_type = "application/pdf"
            extension = "pdf"
        else:
            payload = build_excel_export(app, reviews)
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"

        response = HttpResponse(payload, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{export_filename(app, extension)}"'
        return response
