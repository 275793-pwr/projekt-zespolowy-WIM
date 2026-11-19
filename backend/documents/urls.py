from django.urls import path

from .views import DocumentDetailView, DocumentListCreateView

urlpatterns = [
    path("documents/", DocumentListCreateView.as_view()),
    path("documents/<uuid:pk>/", DocumentDetailView.as_view()),
]
