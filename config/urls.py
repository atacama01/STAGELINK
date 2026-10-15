"""STAGELINK Internship Management — URL routing."""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Domain routers (to be filled as Milestone 2 progresses)
# internships_router = DefaultRouter()
# submissions_router = DefaultRouter()
# notifications_router = DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include([
        # path("internships/", include("internships.urls")),
        # path("submissions/", include("submissions.urls")),
        # path("notifications/", include("notifications.urls")),
        # path("internal/", include("internships.urls_internal")),
    ])),
]
