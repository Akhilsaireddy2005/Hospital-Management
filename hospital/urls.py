from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('patient/admit/', views.PatientAdmissionView.as_view(), name='patient_admit'),
    path('patient/list/', views.PatientListView.as_view(), name='patient_list'),
    path('patient/confirm/<int:pk>/', views.patient_admission_confirm, name='patient_confirm'),
    path('doctor/add/', views.DoctorCreateView.as_view(), name='doctor_add'),
    path('doctor/list/', views.DoctorListView.as_view(), name='doctor_list'),
    path('doctor/update/<int:pk>/', views.DoctorUpdateView.as_view(), name='doctor_update'),
    path('bed/add/', views.BedCreateView.as_view(), name='bed_add'),
    path('optimize/', views.optimize_resources, name='optimize'),
    path('assignment/<int:pk>/', views.assignment_detail, name='assignment_detail'),
] 