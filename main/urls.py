from django.urls import path
from . import views

urlpatterns = [
    # ...existing urls...
    path('update_workflow/', views.update_workflow, name='update_workflow'),
]