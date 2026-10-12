from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("", views.ContentListView.as_view(), name="list"),
    path("<slug:slug>/", views.ContentDetailView.as_view(), name="detail"),
]
