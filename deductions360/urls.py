"""
URL configuration for deductions360 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main.views import index, filtered_chart_data, worklist_view, serve_document, update_workflow, insights_view, daily_transactions_chart_data, rca_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),  # Set this as the homepage URL
    path('filtered-chart-data/', filtered_chart_data, name='filtered_chart_data'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('worklist/', worklist_view, name='worklist'),
    path('documents/<str:doc_type>/<str:invoice_number>/', serve_document, name='serve_document'),
    # path('api/deductions/update/', update_workflow, name='update_deduction'),  # Add this line
    path('update_workflow/', update_workflow, name='update_workflow'),
    path('insights/', insights_view, name='insights'),
    path('rca/', rca_view, name='rca'),
    path('api/daily-transactions/', daily_transactions_chart_data, name='daily-transactions-data'),
    

]
