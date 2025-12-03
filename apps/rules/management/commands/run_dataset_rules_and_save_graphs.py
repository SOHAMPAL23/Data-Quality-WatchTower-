from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset
from apps.rules.tasks import run_dataset_rules_task
from apps.dashboard.models import DashboardGraph
from apps.rules.utils.weekday_checker import is_weekday
import time

class Command(BaseCommand):
    help = 'Run all rules for a dataset and save graph data'

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
            self.stdout.write(self.style.SUCCESS(f'Rule execution result: {result}'))
            
            # Wait a moment for the database to update
            time.sleep(2)
            
            # Check if quality trend data was saved to the dataset
            dataset.refresh_from_db()
            if dataset.quality_trend_data:
                self.stdout.write(self.style.SUCCESS(f'Quality trend data saved to dataset: {len(dataset.quality_trend_data)} entries'))
            else:
                self.stdout.write(self.style.WARNING('No quality trend data saved to dataset'))
            
            # Show recent dashboard graphs
            recent_graphs = DashboardGraph.objects.all().order_by('-created_at')[:5]
            self.stdout.write(self.style.SUCCESS(f'Recently saved graphs:'))
            for graph in recent_graphs:
                self.stdout.write(f'- {graph.graph_type}: {len(graph.data)} entries')
                
        except Dataset.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Dataset with ID {dataset_id} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running dataset rules: {str(e)}'))