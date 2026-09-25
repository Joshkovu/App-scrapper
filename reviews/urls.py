from django.urls import path

from .views import AppListView, ReviewExportView, ReviewListView, ScrapeView

urlpatterns = [
    path("scrape/", ScrapeView.as_view(), name="scrape"),
    path("", AppListView.as_view(), name="apps"),
    path("<uuid:app_id>/reviews/export/", ReviewExportView.as_view(), name="reviews-export"),
    path("<uuid:app_id>/reviews/", ReviewListView.as_view(), name="reviews"),
]
