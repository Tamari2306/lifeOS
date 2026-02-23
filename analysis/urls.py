from django.urls import path
from . import views

app_name = "analysis"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("pdf/", views.export_pdf, name="export_pdf"),
]