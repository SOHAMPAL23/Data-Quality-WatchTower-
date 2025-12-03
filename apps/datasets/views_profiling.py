from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Dataset
from .utils_profiling import profile_dataset, generate_quality_report


@login_required
def dataset_profile(request, dataset_id):
    """Display detailed profile information for a dataset"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # If dataset hasn't been profiled yet, profile it now
    if dataset.quality_score == 0 and not dataset.sample_stats:
        profile_dataset(dataset)
    
    context = {
        'dataset': dataset,
        'column_stats': dataset.sample_stats or {},
        'schema_info': dataset.schema or {},
    }
    
    return render(request, 'datasets/profile.html', context)


@login_required
def dataset_profile_api(request, dataset_id):
    """API endpoint for dataset profile data"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    # Generate fresh profile if needed
    if dataset.quality_score == 0 and not dataset.sample_stats:
        profile_dataset(dataset)
    
    return JsonResponse({
        'id': dataset.id,
        'name': dataset.name,
        'quality_score': float(dataset.quality_score),
        'row_count': dataset.row_count,
        'column_count': dataset.column_count,
        'column_stats': dataset.sample_stats or {},
        'schema_info': dataset.schema or {},
    })


@login_required
def refresh_dataset_profile(request, dataset_id):
    """Refresh the profile for a dataset"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    success = profile_dataset(dataset)
    
    if success:
        return JsonResponse({
            'success': True,
            'message': 'Dataset profile refreshed successfully',
            'quality_score': float(dataset.quality_score),
            'row_count': dataset.row_count,
            'column_count': dataset.column_count,
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Failed to refresh dataset profile'
        }, status=500)


@login_required
def dataset_quality_report(request, dataset_id):
    """Generate and display a detailed quality report"""
    dataset = get_object_or_404(Dataset, id=dataset_id)
    
    report = generate_quality_report(dataset)
    
    if report:
        return JsonResponse(report)
    else:
        return JsonResponse({
            'error': 'Failed to generate quality report'
        }, status=500)