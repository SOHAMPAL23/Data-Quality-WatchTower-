from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.datasets.models import Dataset
from apps.rules.models import Rule
from apps.incidents.models import Incident


@login_required
def global_search(request):
    """Global search across datasets, rules, and incidents"""
    query = request.GET.get('q', '')
    results = {
        'datasets': [],
        'rules': [],
        'incidents': []
    }
    
    if query:
        # Search datasets
        results['datasets'] = Dataset.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()[:10]
        
        # Search rules
        results['rules'] = Rule.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()[:10]
        
        # Search incidents
        results['incidents'] = Incident.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query)
        ).distinct()[:10]
    
    context = {
        'query': query,
        'results': results,
        'total_results': sum(len(results[key]) for key in results)
    }
    
    return render(request, 'search/results.html', context)