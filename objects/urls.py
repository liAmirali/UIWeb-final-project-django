from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.UploadObjectView.as_view(), name="upload-object"),
    path("download/", views.DownloadObjectView.as_view(), name="download-object"),
    path("list/", views.ObjectListView.as_view(), name="list-objects"),
    path("delete/", views.DeleteObject.as_view(), name="delete-object"),
    path("access/", views.AccessUpdateView.as_view(), name="update-access"),
    path("people/", views.UsersAccessView.as_view(), name="people-shared")
]
