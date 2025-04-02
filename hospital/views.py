from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Patient, Doctor, Bed, Equipment, Assignment
from .forms import PatientAdmissionForm, DoctorAvailabilityForm, BedForm, DoctorCreateForm
from .optimizer import run_optimization
from django.db.models import Q

class DashboardView(ListView):
    model = Patient
    template_name = 'hospital/dashboard.html'
    context_object_name = 'recent_patients'

    def get_queryset(self):
        return Patient.objects.all().order_by('-admission_date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['waiting_patients'] = Patient.objects.filter(status='WAI').count()
        context['admitted_patients'] = Patient.objects.filter(status='ADM').count()
        context['treated_patients'] = Patient.objects.filter(status='TRE').count()
        context['discharged_patients'] = Patient.objects.filter(status='DIS').count()
        context['total_patients'] = Patient.objects.count()
        
        # Calculate percentages for progress bars
        total = context['total_patients']
        if total > 0:
            context['waiting_patients_percent'] = (context['waiting_patients'] / total) * 100
            context['admitted_percent'] = (context['admitted_patients'] / total) * 100
            context['discharged_percent'] = (context['discharged_patients'] / total) * 100
        else:
            context['waiting_patients_percent'] = 0
            context['admitted_percent'] = 0
            context['discharged_percent'] = 0
            
        # Add resource stats
        context['available_beds'] = Bed.objects.filter(is_occupied=False).count()
        context['total_beds'] = Bed.objects.count()
        context['available_doctors'] = Doctor.objects.filter(is_available=True).count()
        context['total_doctors'] = Doctor.objects.count()
        context['total_equipment'] = Equipment.objects.count()
        
        if context['total_beds'] > 0:
            context['bed_usage_percent'] = ((context['total_beds'] - context['available_beds']) / context['total_beds']) * 100
        else:
            context['bed_usage_percent'] = 0
            
        return context

class PatientAdmissionView(CreateView):
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

def optimize_resources(request):
    if request.method == 'POST':
        assignments_made = run_optimization()
        if assignments_made > 0:
            messages.success(request, f'{assignments_made} new assignment(s) have been made.')
        else:
            messages.info(request, 'No new assignments could be made at this time.')
        return redirect('hospital:dashboard')
    return redirect('hospital:dashboard')

class PatientListView(ListView):
    model = Patient
    template_name = 'hospital/patient_list.html'
    context_object_name = 'patients'

    def get_queryset(self):
        status = self.request.GET.get('status', '')
        if status:
            return Patient.objects.filter(status=status).order_by('-priority', '-admission_date')
        return Patient.objects.all().order_by('-admission_date')

class DoctorUpdateView(UpdateView):
    model = Doctor
    form_class = DoctorAvailabilityForm
    template_name = 'hospital/doctor_update.html'
    success_url = reverse_lazy('hospital:dashboard')

class BedCreateView(CreateView):
    model = Bed
    form_class = BedForm
    template_name = 'hospital/bed_form.html'
    success_url = reverse_lazy('hospital:dashboard')

def assignment_detail(request, pk):
    assignment = Assignment.objects.get(pk=pk)
    return render(request, 'hospital/assignment_detail.html', {'assignment': assignment})

class DoctorCreateView(CreateView):
    model = Doctor
    form_class = DoctorCreateForm
    template_name = 'hospital/doctor_form.html'
    success_url = reverse_lazy('hospital:doctor_list')

    def form_valid(self, form):
        try:
            # Add debug messages
            messages.info(self.request, f'Processing form data: {form.cleaned_data}')
            
            # Save the form to create the doctor
            response = super().form_valid(form)
            
            # Add success message
            messages.success(self.request, f'Doctor {self.object.user.get_full_name()} has been added successfully.')
            return response
        except Exception as e:
            # Add error message if something goes wrong
            messages.error(self.request, f'Error adding doctor: {e}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Add information about form errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error in {field}: {error}")
        
        return super().form_invalid(form)

class DoctorListView(ListView):
    model = Doctor
    template_name = 'hospital/doctor_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        return Doctor.objects.all().order_by('user__first_name', 'user__last_name')

def patient_admission_confirm(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Get available resources
        available_doctors = Doctor.objects.filter(is_available=True)
        available_beds = Bed.objects.filter(is_occupied=False)
        
        if not available_doctors or not available_beds:
            messages.error(request, f'Cannot admit patient {patient.name}. No available doctors or beds.')
            return redirect('hospital:patient_list')
        
        # Find the most suitable doctor (lowest current patient count)
        # Since current_patients is a property, we need to get all doctors and sort in Python
        doctor = sorted(available_doctors, key=lambda d: d.current_patients)[0] if available_doctors else None
        
        # Find a suitable bed based on patient priority
        if patient.priority >= 4:  # Critical or Emergency patients
            bed = available_beds.filter(
                Q(ward__icontains='ICU') | Q(ward__icontains='Emergency')
            ).first() or available_beds.first()
        else:  # Regular priority patients
            bed = available_beds.filter(
                ~Q(ward__icontains='ICU')
            ).first() or available_beds.first()
        
        if doctor and bed:
            # Update bed status
            bed.is_occupied = True
            bed.save()
            
            # Update patient status
            patient.status = 'ADM'  # Admitted
            patient.assigned_doctor = doctor
            patient.assigned_bed = bed
            patient.save()
            
            # Create assignment record
            Assignment.objects.create(
                patient=patient,
                doctor=doctor,
                bed=bed,
                active=True
            )
            
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

def patient_discharge(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Release the bed if assigned
        if patient.assigned_bed:
            bed = patient.assigned_bed
            bed.is_occupied = False
            bed.save()
            
        # Update assignments to inactive
        Assignment.objects.filter(patient=patient, active=True).update(active=False)
        
        # Update patient status
        patient.status = 'DIS'  # Discharged
        patient.assigned_doctor = None
        patient.assigned_bed = None
        patient.save()
        
        messages.success(request, f'Patient {patient.name} has been successfully discharged.')
        return redirect('hospital:patient_list')
    
    return render(request, 'hospital/patient_discharge_confirm.html', {
        'patient': patient
    })

def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    
    if request.method == 'POST':
        doctor_name = doctor.user.get_full_name()
        user = doctor.user
        
        # Check if doctor has assigned patients
        assigned_patients = Patient.objects.filter(assigned_doctor=doctor)
        if assigned_patients.exists():
            # Update patients to have no assigned doctor
            for patient in assigned_patients:
                patient.assigned_doctor = None
                patient.save()
            
            messages.warning(
                request, 
                f'{assigned_patients.count()} patients were unassigned from Dr. {doctor_name}.'
            )
        
        # Delete the doctor and associated user
        doctor.delete()
        user.delete()
        
        messages.success(request, f'Doctor {doctor_name} has been successfully removed.')
        return redirect('hospital:doctor_list')
    
    # Get number of patients assigned to this doctor for confirmation page
    assigned_patients_count = Patient.objects.filter(assigned_doctor=doctor).count()
    
    return render(request, 'hospital/doctor_delete_confirm.html', {
        'doctor': doctor,
        'assigned_patients_count': assigned_patients_count
    })

def patient_waiting(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Update patient status to waiting
        patient.status = 'WAI'  # Waiting
        
        # If patient was previously admitted, free up resources
        if patient.assigned_bed:
            bed = patient.assigned_bed
            bed.is_occupied = False
            bed.save()
            
        # Clear any doctor/bed assignments
        patient.assigned_doctor = None
        patient.assigned_bed = None
        patient.save()
        
        # Update any active assignments to inactive
        Assignment.objects.filter(patient=patient, active=True).update(active=False)
        
        messages.success(request, f'Patient {patient.name} has been placed in the waiting list.')
        return redirect('hospital:patient_list')
    
    return render(request, 'hospital/patient_waiting_confirm.html', {
        'patient': patient
    })
