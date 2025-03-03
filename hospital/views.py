from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Patient, Doctor, Bed, Equipment, Assignment
from .forms import PatientAdmissionForm, DoctorAvailabilityForm, BedForm, DoctorCreateForm
from .optimizer import run_optimization

class DashboardView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'hospital/dashboard.html'
    context_object_name = 'recent_patients'

    def get_queryset(self):
        return Patient.objects.all().order_by('-admission_date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['waiting_patients'] = Patient.objects.filter(status='WAI').count()
        context['admitted_patients'] = Patient.objects.filter(status='ADM').count()
        context['total_patients'] = Patient.objects.count()
        return context

class PatientAdmissionView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientAdmissionForm
    template_name = 'hospital/patient_admission.html'
    success_url = reverse_lazy('hospital:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Patient {self.object.name} has been added to the waiting list.')
        # Run optimization after adding a new patient
        assignments_made = run_optimization()
        if assignments_made > 0:
            messages.success(self.request, f'{assignments_made} new assignment(s) have been made.')
        return response

@login_required
def optimize_resources(request):
    if request.method == 'POST':
        assignments_made = run_optimization()
        if assignments_made > 0:
            messages.success(request, f'{assignments_made} new assignment(s) have been made.')
        else:
            messages.info(request, 'No new assignments could be made at this time.')
        return redirect('hospital:dashboard')
    return redirect('hospital:dashboard')

class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'hospital/patient_list.html'
    context_object_name = 'patients'

    def get_queryset(self):
        status = self.request.GET.get('status', '')
        if status:
            return Patient.objects.filter(status=status).order_by('-priority', '-admission_date')
        return Patient.objects.all().order_by('-admission_date')

class DoctorUpdateView(LoginRequiredMixin, UpdateView):
    model = Doctor
    form_class = DoctorAvailabilityForm
    template_name = 'hospital/doctor_update.html'
    success_url = reverse_lazy('hospital:dashboard')

class BedCreateView(LoginRequiredMixin, CreateView):
    model = Bed
    form_class = BedForm
    template_name = 'hospital/bed_form.html'
    success_url = reverse_lazy('hospital:dashboard')

@login_required
def assignment_detail(request, pk):
    assignment = Assignment.objects.get(pk=pk)
    return render(request, 'hospital/assignment_detail.html', {'assignment': assignment})

class DoctorCreateView(LoginRequiredMixin, CreateView):
    model = Doctor
    form_class = DoctorCreateForm
    template_name = 'hospital/doctor_form.html'
    success_url = reverse_lazy('hospital:doctor_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Doctor {self.object.user.get_full_name()} has been added successfully.')
        return response

class DoctorListView(LoginRequiredMixin, ListView):
    model = Doctor
    template_name = 'hospital/doctor_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        return Doctor.objects.all().order_by('user__first_name', 'user__last_name')

@login_required
def patient_admission_confirm(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Run optimization for this specific patient
        assignments_made = run_optimization()
        if assignments_made > 0:
            messages.success(request, f'Patient {patient.name} has been successfully admitted.')
        else:
            messages.warning(request, f'Could not find suitable assignment for {patient.name} at this time.')
        return redirect('hospital:patient_list')
    
    # Get available resources
    available_doctors = Doctor.objects.filter(is_available=True)
    available_beds = Bed.objects.filter(is_occupied=False)
    
    return render(request, 'hospital/patient_admission_confirm.html', {
        'patient': patient,
        'available_doctors': available_doctors,
        'available_beds': available_beds
    })
