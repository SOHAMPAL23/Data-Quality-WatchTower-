from django.core.management.base import BaseCommand
from apps.dashboard.api_views import dataset_quality_api, rule_frequency_api, rules_per_dataset_api, recent_rule_executions_api
from apps.dashboard.models import DashboardGraph
from django.http import HttpRequest

class Command(BaseCommand):
    help = 'Test graph data saving functionality'

    def handle(self, *args, **options):
        # Create a mock request
        request = HttpRequest()
        request.method = 'GET'
        
        # Test each API endpoint
        self.stdout.write('Testing dataset quality API...')
        try:
            response = dataset_quality_api(request)
            self.stdout.write(self.style.SUCCESS(f'Dataset quality API response: {response.content.decode()[:100]}...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in dataset quality API: {e}'))
        
        self.stdout.write('Testing rule frequency API...')
        try:
            response = rule_frequency_api(request)
            self.stdout.write(self.style.SUCCESS(f'Rule frequency API response: {response.content.decode()[:100]}...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in rule frequency API: {e}'))
        
        self.stdout.write('Testing rules per dataset API...')
        try:
            response = rules_per_dataset_api(request)
            self.stdout.write(self.style.SUCCESS(f'Rules per dataset API response: {response.content.decode()[:100]}...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in rules per dataset API: {e}'))
        
        self.stdout.write('Testing recent rule executions API...')
        try:
            response = recent_rule_executions_api(request)
            self.stdout.write(self.style.SUCCESS(f'Recent rule executions API response: {response.content.decode()[:100]}...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in recent rule executions API: {e}'))
        
        # Check saved graph data
        graph_count = DashboardGraph.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total saved graphs: {graph_count}'))
        
        # Show recent graphs
        recent_graphs = DashboardGraph.objects.all()[:5]
        for graph in recent_graphs:
            self.stdout.write(f'- {graph.graph_type}: {str(graph.data)[:50]}...')