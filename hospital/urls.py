from django.urls import path
from . import views

app_name = 'hospital'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('patient/admit/', views.PatientAdmissionView.as_view(), name='patient_admit'),
    path('patient/list/', views.PatientListView.as_view(), name='patient_list'),
    path('patient/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patient/confirm/<int:pk>/', views.patient_admission_confirm, name='patient_confirm'),
    path('patient/discharge/<int:pk>/', views.patient_discharge, name='patient_discharge'),
    path('patient/waiting/<int:pk>/', views.patient_waiting, name='patient_waiting'),
    path('patient/export-pdf/', views.export_patients_pdf, name='export_patients_pdf'),
    path('patient/<int:patient_id>/equipment/assign/', views.assign_equipment, name='assign_equipment'),
    path('patient/<int:patient_id>/equipment/<int:equipment_id>/unassign/', views.unassign_equipment, name='unassign_equipment'),
    path('patient/<int:patient_id>/doctor/assign/', views.assign_doctor, name='assign_doctor'),
    path('patient/<int:patient_id>/doctor/unassign/', views.unassign_doctor, name='unassign_doctor'),
    path('doctor/add/', views.DoctorCreateView.as_view(), name='doctor_add'),
    path('doctor/list/', views.DoctorListView.as_view(), name='doctor_list'),
    path('doctor/update/<int:pk>/', views.DoctorUpdateView.as_view(), name='doctor_update'),
    path('doctor/delete/<int:pk>/', views.doctor_delete, name='doctor_delete'),
    path('bed/add/', views.BedCreateView.as_view(), name='bed_add'),
    path('optimize/', views.optimize_resources, name='optimize'),
    path('assignment/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('bed-availability/', views.bed_availability_view, name='bed_availability'),
    path('doctor-patients/', views.doctor_patients_view, name='doctor_patients'),
] 