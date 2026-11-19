from django.urls import include, path

urlpatterns = [
    path("api/", include("accounts.urls")),
    path("api/", include("documents.urls")),
    path("api/", include("chat.urls")),
]
