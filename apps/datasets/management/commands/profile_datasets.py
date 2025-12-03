from django.core.management.base import BaseCommand
from apps.datasets.models import Dataset
from apps.datasets.utils_profiling import profile_dataset


class Command(BaseCommand):
    help = 'Profile all datasets and update their statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset-id',
            type=int,
            help='Profile a specific dataset by ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Profile all datasets',
        )

    def handle(self, *args, **options):
        if options['dataset_id']:
            try:
                dataset = Dataset.objects.get(id=options['dataset_id'])
                self.stdout.write(f'Profiling dataset: {dataset.name}')
                if profile_dataset(dataset):
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully profiled dataset: {dataset.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to profile dataset: {dataset.name}')
                    )
            except Dataset.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Dataset with ID {options["dataset_id"]} does not exist')
                )
        elif options['all']:
            datasets = Dataset.objects.all()
            self.stdout.write(f'Profiling {len(datasets)} datasets...')
            
            success_count = 0
            for dataset in datasets:
                self.stdout.write(f'Profiling dataset: {dataset.name}')
                if profile_dataset(dataset):
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Successfully profiled {dataset.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ Failed to profile {dataset.name}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Profiled {success_count}/{len(datasets)} datasets successfully'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify either --dataset-id or --all flag. '
                    'Use --help for more information.'
                )
            )