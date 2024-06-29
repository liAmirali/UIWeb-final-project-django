from django.urls import path, include

urlpatterns = [
    path("auth/", include("user.urls")),
    path("objects/", include("objects.urls")),
]
