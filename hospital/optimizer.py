from pulp import *
from .models import Doctor, Bed, Patient, Equipment, Assignment
from django.db.models import Q
from datetime import datetime, date, timedelta

def optimize_assignments():
    """
    Optimize the assignment of patients to doctors and beds using Integer Linear Programming.
    Returns a list of tuples (patient, doctor, bed) representing optimal assignments.
    """
    # Get all available resources and waiting patients
    waiting_patients = Patient.objects.filter(status='WAI').order_by('-priority')
    available_doctors = Doctor.objects.filter(is_available=True)
    available_beds = Bed.objects.filter(is_occupied=False)
    
    if not (waiting_patients and available_doctors and available_beds):
        return []

    # Create the optimization problem
    prob = LpProblem("Hospital_Assignment", LpMaximize)

    # Decision Variables
    # x[i,j,k] = 1 if patient i is assigned to doctor j and bed k
    x = LpVariable.dicts("assignment",
                        ((p.id, d.id, b.id) 
                         for p in waiting_patients
                         for d in available_doctors
                         for b in available_beds),
                        cat='Binary')

    # Objective Function: Maximize priority-weighted assignments
    prob += lpSum(x[p.id, d.id, b.id] * p.priority
                 for p in waiting_patients
                 for d in available_doctors
                 for b in available_beds)

    # Constraints
    # 1. Each patient can be assigned to at most one doctor and one bed
    for p in waiting_patients:
        prob += lpSum(x[p.id, d.id, b.id]
                     for d in available_doctors
                     for b in available_beds) <= 1

    # 2. Each doctor cannot exceed their maximum patient capacity
    for d in available_doctors:
        prob += lpSum(x[p.id, d.id, b.id]
                     for p in waiting_patients
                     for b in available_beds) <= d.max_patients - d.current_patients

    # 3. Each bed can be assigned to at most one patient
    for b in available_beds:
        prob += lpSum(x[p.id, d.id, b.id]
                     for p in waiting_patients
                     for d in available_doctors) <= 1

    # 4. Bed type constraints (match patient priority with bed type)
    for p in waiting_patients:
        for d in available_doctors:
            for b in available_beds:
                if p.priority >= 4 and b.bed_type != 'ICU':  # Critical patients need ICU
                    prob += x[p.id, d.id, b.id] == 0
                elif p.priority <= 1 and b.bed_type == 'ICU':  # Low priority patients don't need ICU
                    prob += x[p.id, d.id, b.id] == 0

    # Solve the problem
    prob.solve()

    # Extract results if optimal solution found
    if LpStatus[prob.status] == 'Optimal':
        assignments = []
        for p in waiting_patients:
            for d in available_doctors:
                for b in available_beds:
                    if value(x[p.id, d.id, b.id]) == 1:
                        assignments.append((p, d, b))
        return assignments
    return []

def apply_assignments(assignments):
    """
    Apply the optimized assignments to the database.
    """
    for patient, doctor, bed in assignments:
        # Update bed status
        bed.is_occupied = True
        bed.save()

        # Update doctor's patient count
        doctor.current_patients += 1
        doctor.save()

        # Update patient status and assignments
        patient.status = 'ADM'  # Admitted
        patient.assigned_doctor = doctor
        patient.assigned_bed = bed
        patient.save()

        # Create assignment record
        Assignment.objects.create(
            patient=patient,
            doctor=doctor,
            bed=bed,
            expected_end_date=date.today() + timedelta(days=patient.expected_stay_days),
            priority_score=patient.priority
        )

def run_optimization():
    """
    Main function to run the optimization process.
    Returns the number of successful assignments made.
    """
    assignments = optimize_assignments()
    if assignments:
        apply_assignments(assignments)
    return len(assignments) 