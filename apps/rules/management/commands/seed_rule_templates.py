from django.core.management.base import BaseCommand
from apps.rules.models import RuleTemplate

class Command(BaseCommand):
    help = 'Seed predefined rule templates'

    def handle(self, *args, **options):
        # Define predefined rule templates
        templates = [
            {
                'name': 'Missing Value Check',
                'description': 'Check for missing/null values in specified columns',
                'template_type': 'MISSING_VALUE',
                'dsl_template': "NOT_NULL('{column_name}')",
                'severity': 'HIGH'
            },
            {
                'name': 'Duplicate Detection',
                'description': 'Detect duplicate records based on specified columns',
                'template_type': 'DUPLICATE_DETECTION',
                'dsl_template': "UNIQUE('{column_name}')",
                'severity': 'MEDIUM'
            },
            {
                'name': 'Outlier Detection',
                'description': 'Identify outliers in numerical columns using statistical methods',
                'template_type': 'OUTLIER_DETECTION',
                'dsl_template': "IN_RANGE('{column_name}', {min_value}, {max_value})",
                'severity': 'MEDIUM'
            },
            {
                'name': 'Schema Validation',
                'description': 'Validate that columns conform to expected data types and formats',
                'template_type': 'SCHEMA_VALIDATION',
                'dsl_template': "REGEX('{column_name}', '{pattern}')",
                'severity': 'HIGH'
            },
            {
                'name': 'Length Validation',
                'description': 'Check that text fields have appropriate lengths',
                'template_type': 'CUSTOM',
                'dsl_template': "LENGTH_RANGE('{column_name}', {min_length}, {max_length})",
                'severity': 'LOW'
            }
        ]

        # Create templates
        created_count = 0
        for template_data in templates:
            # Check if template already exists
            if not RuleTemplate.objects.filter(name=template_data['name']).exists():
                RuleTemplate.objects.create(**template_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created template: {template_data['name']}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Template already exists: {template_data['name']}")
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {created_count} rule templates')
        )