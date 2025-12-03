from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset
from apps.rules.tasks import run_dataset_rules_task
from apps.rules.utils.weekday_checker import is_weekday

class Command(BaseCommand):
    help = 'Run all rules for a specific dataset'

    def add_arguments(self, parser):
        parser.add_argument('dataset_id', type=int, help='ID of the dataset to run rules for')

    def handle(self, *args, **options):
        # Check if it's a weekday before running
        if not is_weekday():
            self.stdout.write(self.style.WARNING('Weekend detected. Rule execution is only allowed on weekdays (Mon-Fri).'))
            return
        
        dataset_id = options['dataset_id']
        
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            self.stdout.write(f'Running rules for dataset: {dataset.name}')
            
            # Run the task synchronously for immediate feedback
            result = run_dataset_rules_task(dataset_id)
            self.stdout.write(f'Result: {result}')
            
        except Dataset.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Dataset with ID {dataset_id} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running dataset rules: {str(e)}'))