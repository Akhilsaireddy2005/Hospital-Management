from django.contrib import admin
from .models import Patient, Doctor, Bed, Equipment, Assignment

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'status', 'priority', 'admission_date')
    list_filter = ('status', 'priority', 'admission_date')
    search_fields = ('name', 'condition')
    readonly_fields = ('admission_date',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'is_available', 'max_patients', 'current_patients')
    list_filter = ('specialty', 'is_available')
    search_fields = ('user__first_name', 'user__last_name', 'specialty')

@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('number', 'ward', 'is_occupied')
    list_filter = ('is_occupied', 'ward')
    search_fields = ('number', 'ward')

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'status', 'last_maintenance', 'next_maintenance')
    list_filter = ('equipment_type', 'status')
    search_fields = ('name',)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'bed', 'assigned_date', 'active')
    list_filter = ('active', 'assigned_date')
    search_fields = ('patient__name', 'doctor__user__first_name', 'doctor__user__last_name')
