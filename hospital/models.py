from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialty = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    max_patients = models.IntegerField(default=5)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    @property
    def current_patients(self):
        return self.assignment_set.filter(active=True).count()

class Bed(models.Model):
    number = models.CharField(max_length=10, unique=True)
    is_occupied = models.BooleanField(default=False)
    ward = models.CharField(max_length=50)

    def __str__(self):
        return f"Bed {self.number} ({self.ward})"

class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('MON', 'Monitoring Equipment'),
        ('DIA', 'Diagnostic Equipment'),
        ('THE', 'Therapeutic Equipment'),
        ('LIF', 'Life Support Equipment'),
        ('OTH', 'Other'),
    ]

    STATUS_CHOICES = [
        ('AV', 'Available'),
        ('UM', 'Under Maintenance'),
        ('NA', 'Not Available'),
    ]

    name = models.CharField(max_length=100)
    equipment_type = models.CharField(max_length=3, choices=EQUIPMENT_TYPES)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='AV')
    last_maintenance = models.DateTimeField(null=True, blank=True)
    next_maintenance = models.DateTimeField(null=True, blank=True)
    maintenance_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"

class Patient(models.Model):
    STATUS_CHOICES = [
        ('WAI', 'Waiting'),
        ('ADM', 'Admitted'),
        ('TRE', 'Under Treatment'),
        ('DIS', 'Discharged'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
        (5, 'Emergency'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    name = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(150)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    admission_date = models.DateTimeField(auto_now_add=True)
    condition = models.TextField()
    diagnosis = models.TextField(blank=True)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='WAI')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1)
    expected_stay_days = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    notes = models.TextField(blank=True)
    required_equipment = models.JSONField(default=list, blank=True)
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class Assignment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE)
    assigned_date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient.name} - Dr. {self.doctor.user.get_full_name()}"
