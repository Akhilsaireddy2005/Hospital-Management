from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hospital.models import Doctor
import random

class Command(BaseCommand):
    help = 'Creates a sample doctor for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            help='First name of the doctor',
            default=None,
        )

    def handle(self, *args, **options):
        first_name = options['name'] or random.choice(["John", "Jane", "David", "Sarah", "Robert", "Mary"])
        last_name = random.choice(["Smith", "Johnson", "Williams", "Jones", "Brown", "Miller"])
        username = f"{first_name.lower()}{last_name.lower()}"
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            username = f"{username}{random.randint(1, 999)}"
            
        self.stdout.write(f"Creating doctor: {first_name} {last_name} (username: {username})")
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=f"{username}@hospital.com",
                password="doctor123",
                first_name=first_name,
                last_name=last_name
            )
            
            # Create doctor
            specialty = random.choice([
                "General Medicine", 
                "Cardiology", 
                "Pediatrics", 
                "Orthopedics", 
                "Neurology"
            ])
            
            doctor = Doctor.objects.create(
                user=user,
                specialty=specialty,
                is_available=True,
                max_patients=random.randint(3, 10)
            )
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully created doctor: {doctor} with specialty: {specialty}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating doctor: {e}")) 