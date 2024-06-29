from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.UploadObjectView.as_view(), name="upload-object"),
    path("list/", views.ListObjects.as_view(), name="list-objects"),
]
