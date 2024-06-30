from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.UploadObjectView.as_view(), name="upload-object"),
    path("list/", views.ObjectListView.as_view(), name="list-objects"),
    path("delete/", views.DeleteObject.as_view(), name="delete-object"),
]
