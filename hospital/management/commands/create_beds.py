from django.core.management.base import BaseCommand
from hospital.models import Bed

class Command(BaseCommand):
    help = 'Creates sample beds for the hospital system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating beds...')
        
        # Create some general ward beds
        for i in range(1, 4):
            bed, created = Bed.objects.get_or_create(
                number=f'GEN-{i}',
                defaults={
                    'ward': 'General Ward',
                    'is_occupied': False
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created bed: {bed}"))
            else:
                self.stdout.write(self.style.WARNING(f"Bed already exists: {bed}"))
        
        # Create some ICU beds
        for i in range(1, 3):
            bed, created = Bed.objects.get_or_create(
                number=f'ICU-{i}',
                defaults={
                    'ward': 'ICU',
                    'is_occupied': False
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created bed: {bed}"))
            else:
                self.stdout.write(self.style.WARNING(f"Bed already exists: {bed}"))
        
        # Create some emergency beds
        for i in range(1, 3):
            bed, created = Bed.objects.get_or_create(
                number=f'ER-{i}',
                defaults={
                    'ward': 'Emergency',
                    'is_occupied': False
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created bed: {bed}"))
            else:
                self.stdout.write(self.style.WARNING(f"Bed already exists: {bed}"))
                
        self.stdout.write(self.style.SUCCESS('Bed creation complete!')) 