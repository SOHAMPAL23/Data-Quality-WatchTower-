from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset
import os

class Command(BaseCommand):
    help = 'Clean up dataset records that point to missing files'

    def handle(self, *args, **options):
        # Get all datasets
        datasets = Dataset.objects.all()
        deleted_count = 0
        
        for dataset in datasets:
            # Check if the file exists
            if dataset.file and not os.path.exists(dataset.file.path):
                # File doesn't exist, delete the dataset record
                dataset_name = dataset.name
                dataset.delete()
                deleted_count += 1
                self.stdout.write(self.style.SUCCESS(f'Deleted dataset "{dataset_name}" (missing file)'))
        
        if deleted_count == 0:
            self.stdout.write('No datasets with missing files found')
        else:
            self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} datasets with missing files'))