from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Patient, Doctor, Bed, Equipment, Assignment, EquipmentAssignment
from .forms import PatientAdmissionForm, DoctorAvailabilityForm, BedForm, DoctorCreateForm, EquipmentAssignmentForm
from .optimizer import run_optimization
from django.db.models import Q
import csv
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from reportlab.pdfgen import canvas
from datetime import datetime
from django.contrib.auth.decorators import login_required

class DashboardView(ListView):
    model = Patient
    template_name = 'hospital/dashboard.html'
    context_object_name = 'recent_patients'

    def get_queryset(self):
        return Patient.objects.all().order_by('-admission_date')[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['waiting_patients'] = Patient.objects.filter(status='WAI').count()
        context['admitted_patients'] = Patient.objects.filter(status='TRE').count()
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
            
        if context['total_doctors'] > 0:
            context['doctor_availability_percent'] = (context['available_doctors'] / context['total_doctors']) * 100
        else:
            context['doctor_availability_percent'] = 0
            
        return context

class PatientAdmissionView(CreateView):
    model = Patient
    form_class = PatientAdmissionForm
    template_name = 'hospital/patient_admission.html'
    success_url = reverse_lazy('hospital:patient_list')

    def form_valid(self, form):
        # Set initial status to waiting
        form.instance.status = 'WAI'
        response = super().form_valid(form)
        messages.success(self.request, f'Patient {self.object.name} has been added to the waiting list.')
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
            patient.status = 'TRE'  # Under Treatment instead of ADM
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
            
            messages.success(request, f'Patient {patient.name} has been successfully admitted and is under treatment.')
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

def bed_availability_view(request):
    # Check if export is requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bed_availability_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Ward', 'Bed Number', 'Status', 'Last Updated'])
        
        for bed in Bed.objects.all().order_by('ward', 'number'):
            writer.writerow([
                bed.ward,
                bed.number,
                'Occupied' if bed.is_occupied else 'Available',
                bed.updated_at.strftime('%Y-%m-%d %H:%M:%S') if bed.updated_at else 'N/A'
            ])
        
        return response
    
    # Get all beds grouped by ward
    beds_by_ward = {}
    for bed in Bed.objects.all().order_by('ward', 'number'):
        if bed.ward not in beds_by_ward:
            beds_by_ward[bed.ward] = []
        beds_by_ward[bed.ward].append(bed)
    
    # Calculate statistics
    total_beds = Bed.objects.count()
    available_beds = Bed.objects.filter(is_occupied=False).count()
    occupied_beds = total_beds - available_beds
    
    context = {
        'beds_by_ward': beds_by_ward,
        'total_beds': total_beds,
        'available_beds': available_beds,
        'occupied_beds': occupied_beds,
        'bed_usage_percent': (occupied_beds / total_beds * 100) if total_beds > 0 else 0
    }
    
    return render(request, 'hospital/bed_availability.html', context)

def doctor_patients_view(request):
    # Get all doctors with their assigned patients
    doctors = Doctor.objects.prefetch_related('patient_set').all()
    
    context = {
        'doctors': doctors,
    }
    return render(request, 'hospital/doctor_patients.html', context)

def export_patients_pdf(request):
    # Get all patients including discharged ones
    patients = Patient.objects.all().order_by('-admission_date')
    
    # Create a BytesIO buffer for the PDF
    buffer = BytesIO()
    
    # Create the PDF object with smaller margins for more space
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1  # Center alignment
    )
    
    # Create custom styles for cells with smaller font size
    normal_style = ParagraphStyle(
        'NormalWithWrap',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=0  # Left alignment
    )
    
    center_style = ParagraphStyle(
        'CenterWithWrap',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=1  # Center alignment
    )
    
    # Add hospital title
    elements.append(Paragraph("Hospital Patient List", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                            ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, alignment=1)))
    elements.append(Spacer(1, 10))
    
    # Define the table data with paragraphs for wrapping
    data = [[
        Paragraph('ID', center_style),
        Paragraph('Name', center_style),
        Paragraph('Status', center_style),
        Paragraph('Priority', center_style),
        Paragraph('Doctor', center_style),
        Paragraph('Equipment', center_style),
        Paragraph('Admission Date', center_style),
        Paragraph('Actions', center_style)
    ]]
    
    # Add patient data
    for patient in patients:
        # Format doctor name
        doctor_name = f"Dr. {patient.assigned_doctor.user.get_full_name()}" if patient.assigned_doctor else "Not assigned"
        
        # Format equipment list
        equipment_list = ", ".join(patient.required_equipment) if patient.required_equipment else "No equipment required"
        
        # Get status for actions column
        status_map = {
            'WAI': 'Waiting',
            'ADM': 'Admitted',
            'TRE': 'Under Treatment',
            'DIS': 'Discharged'
        }
        action_status = status_map.get(patient.status, 'Unknown')
        
        # Add row data with paragraphs for wrapping
        data.append([
            Paragraph(f"#{patient.id}", center_style),
            Paragraph(patient.name, normal_style),
            Paragraph(patient.get_status_display(), center_style),
            Paragraph(patient.get_priority_display(), center_style),
            Paragraph(doctor_name, normal_style),
            Paragraph(equipment_list, normal_style),
            Paragraph(patient.admission_date.strftime("%Y-%m-%d %H:%M"), center_style),
            Paragraph(action_status, center_style)  # Show current status in Actions column
        ])
    
    # Create the table with adjusted column widths
    # Added width for Actions column
    table = Table(data, colWidths=[35, 120, 70, 60, 120, 120, 80, 80])
    
    # Add style to the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWHEIGHT', (0, 0), (-1, -1), 35),  # Slightly increased for action lists
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        # Add zebra striping
        *[('BACKGROUND', (0, i), (-1, i), colors.lightgrey) for i in range(2, len(data), 2)],
        # Add borders
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(table)
    
    # Generate the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HttpResponse object with the appropriate PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="patient_list_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    response.write(pdf)
    return response

def assign_equipment(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    assigned_equipment = EquipmentAssignment.objects.filter(patient=patient, active=True).values_list('equipment_id', flat=True)
    available_equipment = Equipment.objects.filter(status='AV')
    
    if request.method == 'POST':
        form = EquipmentAssignmentForm(request.POST)
        if form.is_valid():
            equipment = form.cleaned_data['equipment']
            
            # Check if equipment is already assigned
            if equipment.id in assigned_equipment:
                messages.warning(request, f'Equipment {equipment.name} is already assigned to this patient.')
                return redirect('hospital:patient_detail', pk=patient_id)
            
            # Create new assignment
            EquipmentAssignment.objects.create(
                patient=patient,
                equipment=equipment,
                assigned_by=request.user,
                active=True
            )
            
            # Update equipment status
            equipment.status = 'AS'
            equipment.save()
            
            messages.success(request, f'Equipment {equipment.name} has been assigned to {patient.name}.')
            return redirect('hospital:patient_detail', pk=patient_id)
    else:
        form = EquipmentAssignmentForm()
    
    return render(request, 'hospital/assign_equipment.html', {
        'form': form,
        'patient': patient,
        'assigned_equipment': EquipmentAssignment.objects.filter(patient=patient, active=True),
        'available_equipment': available_equipment
    })

def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    available_doctors = Doctor.objects.filter(is_available=True).order_by('user__first_name', 'user__last_name')
    return render(request, 'hospital/patient_detail.html', {
        'patient': patient,
        'available_doctors': available_doctors
    })

def unassign_equipment(request, patient_id, equipment_id):
    patient = get_object_or_404(Patient, id=patient_id)
    equipment = get_object_or_404(Equipment, id=equipment_id)
    
    if request.method == 'POST':
        # Find and deactivate the assignment
        assignment = EquipmentAssignment.objects.filter(
            patient=patient,
            equipment=equipment,
            active=True
        ).first()
        
        if assignment:
            assignment.active = False
            assignment.save()
            
            # Update equipment status
            equipment.status = 'AV'
            equipment.save()
            
            messages.success(request, f'Equipment {equipment.name} has been unassigned from {patient.name}.')
        else:
            messages.warning(request, f'Equipment {equipment.name} was not assigned to {patient.name}.')
        
        return redirect('hospital:patient_detail', pk=patient_id)
    
    return render(request, 'hospital/unassign_equipment_confirm.html', {
        'patient': patient,
        'equipment': equipment
    })

def assign_doctor(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    available_doctors = Doctor.objects.filter(is_available=True)
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        if doctor_id:
            doctor = get_object_or_404(Doctor, id=doctor_id)
            
            # Update patient's assigned doctor
            patient.assigned_doctor = doctor
            patient.save()
            
            # Create assignment record
            Assignment.objects.create(
                patient=patient,
                doctor=doctor,
                bed=patient.assigned_bed,
                active=True
            )
            
            messages.success(request, f'Doctor {doctor.user.get_full_name()} has been assigned to {patient.name}.')
            return redirect('hospital:patient_detail', pk=patient_id)
        else:
            messages.error(request, 'Please select a doctor.')
    
    return render(request, 'hospital/assign_doctor.html', {
        'patient': patient,
        'available_doctors': available_doctors
    })

def unassign_doctor(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        if patient.assigned_doctor:
            doctor_name = patient.assigned_doctor.user.get_full_name()
            
            # Update assignments to inactive
            Assignment.objects.filter(patient=patient, active=True).update(active=False)
            
            # Clear doctor assignment
            patient.assigned_doctor = None
            patient.save()
            
            messages.success(request, f'Doctor {doctor_name} has been unassigned from {patient.name}.')
        else:
            messages.warning(request, f'No doctor was assigned to {patient.name}.')
        
        return redirect('hospital:patient_detail', pk=patient_id)
    
    return render(request, 'hospital/unassign_doctor_confirm.html', {
        'patient': patient
    })

def dashboard(request):
    # Get counts
    waiting_patients = Patient.objects.filter(status='WAI').count()
    admitted_patients = Patient.objects.filter(status='TRE').count()
    treated_patients = Patient.objects.filter(status='TRE').count()
    discharged_patients = Patient.objects.filter(status='DIS').count()
    total_patients = Patient.objects.count()
    
    # Calculate percentages for progress bars
    if total_patients > 0:
        waiting_patients_percent = (waiting_patients / total_patients) * 100
        admitted_percent = (admitted_patients / total_patients) * 100
        discharged_percent = (discharged_patients / total_patients) * 100
    else:
        waiting_patients_percent = 0
        admitted_percent = 0
        discharged_percent = 0
    
    # Add resource stats
    available_beds = Bed.objects.filter(is_occupied=False).count()
    total_beds = Bed.objects.count()
    available_doctors = Doctor.objects.filter(is_available=True).count()
    total_doctors = Doctor.objects.count()
    total_equipment = Equipment.objects.count()
    
    if total_beds > 0:
        bed_usage_percent = ((total_beds - available_beds) / total_beds) * 100
    else:
        bed_usage_percent = 0
    
    if total_doctors > 0:
        doctor_availability_percent = (available_doctors / total_doctors) * 100
    else:
        doctor_availability_percent = 0
    
    context = {
        'waiting_patients': waiting_patients,
        'admitted_patients': admitted_patients,
        'treated_patients': treated_patients,
        'discharged_patients': discharged_patients,
        'total_patients': total_patients,
        'waiting_patients_percent': waiting_patients_percent,
        'admitted_percent': admitted_percent,
        'discharged_percent': discharged_percent,
        'available_beds': available_beds,
        'total_beds': total_beds,
        'available_doctors': available_doctors,
        'total_doctors': total_doctors,
        'total_equipment': total_equipment,
        'bed_usage_percent': bed_usage_percent,
        'doctor_availability_percent': doctor_availability_percent,
        'recent_patients': Patient.objects.all().order_by('-admission_date')[:10]
    }
    
    return render(request, 'hospital/dashboard.html', context)
