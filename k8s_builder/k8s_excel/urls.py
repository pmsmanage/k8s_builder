from django.urls import path
from . import views

urlpatterns = [
    path('yaml/', views.ExcelToYamlView.as_view(), name='excel-yaml'),
]
