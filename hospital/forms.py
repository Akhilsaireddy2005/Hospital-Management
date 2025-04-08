from django import forms
from django.contrib.auth.models import User
from .models import Patient, Doctor, Bed, Equipment

class PatientAdmissionForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'condition', 'diagnosis', 'priority', 'expected_stay_days', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'condition': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'expected_stay_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Get the selected equipment from POST data
        required_equipment = self.data.getlist('required_equipment')
        instance.required_equipment = required_equipment
        if commit:
            instance.save()
        return instance

class DoctorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['is_available']

class BedForm(forms.ModelForm):
    class Meta:
        model = Bed
        fields = ['number', 'ward']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DoctorCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Doctor
        fields = ['specialty', 'max_patients']
        widgets = {
            'specialty': forms.TextInput(attrs={'class': 'form-control'}),
            'max_patients': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        doctor = super().save(commit=False)
        doctor.user = user
        if commit:
            doctor.save()
        return doctor

class EquipmentAssignmentForm(forms.ModelForm):
    equipment = forms.ModelMultipleChoiceField(
        queryset=Equipment.objects.filter(status='AV'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )

    class Meta:
        model = Patient
        fields = ['required_equipment']
        widgets = {
            'required_equipment': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Set initial equipment based on patient's required_equipment
            self.fields['equipment'].initial = self.instance.required_equipment

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Update the required_equipment field with selected equipment
        instance.required_equipment = [str(eq.id) for eq in self.cleaned_data['equipment']]
        if commit:
            instance.save()
        return instance 