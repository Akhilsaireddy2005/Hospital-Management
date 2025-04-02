from django.contrib.auth.models import User
from hospital.models import Doctor

# Create doctor 1
try:
    user1 = User.objects.create_user(
        username='drsmith',
        email='smith@hospital.com',
        password='doctor123',
        first_name='John',
        last_name='Smith'
    )
    doctor1 = Doctor.objects.create(
        user=user1,
        specialty='General Medicine',
        is_available=True,
        max_patients=5
    )
    print(f"Created doctor: {doctor1}")
except Exception as e:
    print(f"Error creating doctor 1: {e}")

# Create doctor 2
try:
    user2 = User.objects.create_user(
        username='drpatel',
        email='patel@hospital.com',
        password='doctor123',
        first_name='Divya',
        last_name='Patel'
    )
    doctor2 = Doctor.objects.create(
        user=user2,
        specialty='Cardiology',
        is_available=True,
        max_patients=4
    )
    print(f"Created doctor: {doctor2}")
except Exception as e:
    print(f"Error creating doctor 2: {e}")

# Create doctor 3
try:
    user3 = User.objects.create_user(
        username='drwilson',
        email='wilson@hospital.com',
        password='doctor123',
        first_name='Robert',
        last_name='Wilson'
    )
    doctor3 = Doctor.objects.create(
        user=user3,
        specialty='Pediatrics',
        is_available=True,
        max_patients=6
    )
    print(f"Created doctor: {doctor3}")
except Exception as e:
    print(f"Error creating doctor 3: {e}")

print("Doctor creation complete!") 