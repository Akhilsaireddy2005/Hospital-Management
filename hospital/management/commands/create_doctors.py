from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hospital.models import Doctor

class Command(BaseCommand):
    help = 'Creates sample doctors for the hospital system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating doctors...')
        
        # Create doctor 1
        try:
            user1, created = User.objects.get_or_create(
                username='drsmith',
                defaults={
                    'email': 'smith@hospital.com',
                    'first_name': 'John',
                    'last_name': 'Smith'
                }
            )
            if created:
                user1.set_password('doctor123')
                user1.save()
                
            doctor1, doc_created = Doctor.objects.get_or_create(
                user=user1,
                defaults={
                    'specialty': 'General Medicine',
                    'is_available': True,
                    'max_patients': 5
                }
            )
            if doc_created:
                self.stdout.write(self.style.SUCCESS(f"Created doctor: {doctor1}"))
            else:
                self.stdout.write(self.style.WARNING(f"Doctor already exists: {doctor1}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating doctor 1: {e}"))

        # Create doctor 2
        try:
            user2, created = User.objects.get_or_create(
                username='drpatel',
                defaults={
                    'email': 'patel@hospital.com',
                    'first_name': 'Divya',
                    'last_name': 'Patel'
                }
            )
            if created:
                user2.set_password('doctor123')
                user2.save()
                
            doctor2, doc_created = Doctor.objects.get_or_create(
                user=user2,
                defaults={
                    'specialty': 'Cardiology',
                    'is_available': True,
                    'max_patients': 4
                }
            )
            if doc_created:
                self.stdout.write(self.style.SUCCESS(f"Created doctor: {doctor2}"))
            else:
                self.stdout.write(self.style.WARNING(f"Doctor already exists: {doctor2}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating doctor 2: {e}"))

        # Create doctor 3
        try:
            user3, created = User.objects.get_or_create(
                username='drwilson',
                defaults={
                    'email': 'wilson@hospital.com',
                    'first_name': 'Robert',
                    'last_name': 'Wilson'
                }
            )
            if created:
                user3.set_password('doctor123')
                user3.save()
                
            doctor3, doc_created = Doctor.objects.get_or_create(
                user=user3,
                defaults={
                    'specialty': 'Pediatrics',
                    'is_available': True,
                    'max_patients': 6
                }
            )
            if doc_created:
                self.stdout.write(self.style.SUCCESS(f"Created doctor: {doctor3}"))
            else:
                self.stdout.write(self.style.WARNING(f"Doctor already exists: {doctor3}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating doctor 3: {e}"))

        self.stdout.write(self.style.SUCCESS('Doctor creation complete!')) 