import pandas as pd
import numpy as np
from django.conf import settings
import json
import os
from .models import Dataset


def profile_dataset(dataset):
    """
    Profile a dataset and update its metadata with statistics
    """
    try:
        # Load dataset data
        df = load_dataset_data(dataset)
        
        if df is None or df.empty:
            return False
            
        # Calculate basic statistics
        row_count = len(df)
        column_count = len(df.columns)
        
        # Calculate quality score
        quality_score = calculate_quality_score(df)
        
        # Get column statistics
        column_stats = get_column_statistics(df)
        
        # Get schema information
        schema_info = get_schema_info(df)
        
        # Update dataset object
        dataset.row_count = row_count
        dataset.column_count = column_count
        dataset.quality_score = quality_score
        dataset.sample_stats = column_stats
        dataset.schema = schema_info
        
        dataset.save()
        
        return True
        
    except Exception as e:
        print(f"Error profiling dataset {dataset.name}: {str(e)}")
        return False


def load_dataset_data(dataset):
    """
    Load dataset data into a pandas DataFrame
    """
    try:
        if dataset.source_type == 'CSV' and dataset.file:
            # Load CSV file
            file_path = dataset.file.path
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                return df
        elif dataset.source_type == 'DB' and dataset.db_connection:
            # Load from database (simplified implementation)
            # In a real implementation, this would connect to the actual database
            pass
            
        return None
    except Exception as e:
        print(f"Error loading dataset {dataset.name}: {str(e)}")
        return None


def calculate_quality_score(df):
    """
    Calculate an overall quality score for the dataset (0-100)
    """
    if df.empty:
        return 0.0
    
    # Factors for quality score calculation:
    # 1. Completeness (missing values) - 40%
    # 2. Uniqueness (duplicate rows) - 30%
    # 3. Consistency (data types) - 20%
    # 4. Validity (schema adherence) - 10%
    
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    completeness_score = (1 - (missing_cells / total_cells)) * 40 if total_cells > 0 else 0
    
    # Check for duplicate rows
    duplicate_rows = df.duplicated().sum()
    uniqueness_score = (1 - (duplicate_rows / len(df))) * 30 if len(df) > 0 else 0
    
    # Simple consistency check (basic)
    consistency_score = 20  # Placeholder
    
    # Validity score (basic)
    validity_score = 10  # Placeholder
    
    quality_score = completeness_score + uniqueness_score + consistency_score + validity_score
    return round(quality_score, 2)


def get_column_statistics(df):
    """
    Get detailed statistics for each column
    """
    stats = {}
    
    for column in df.columns:
        col_data = df[column]
        col_stats = {
            'name': column,
            'dtype': str(col_data.dtype),
            'non_null_count': int(col_data.count()),
            'null_count': int(col_data.isnull().sum()),
            'unique_count': int(col_data.nunique()),
            'null_percentage': round((col_data.isnull().sum() / len(df)) * 100, 2) if len(df) > 0 else 0
        }
        
        # Add type-specific statistics
        if col_data.dtype in ['int64', 'float64']:
            col_stats.update({
                'min': float(col_data.min()) if not col_data.isnull().all() else None,
                'max': float(col_data.max()) if not col_data.isnull().all() else None,
                'mean': float(col_data.mean()) if not col_data.isnull().all() else None,
                'std': float(col_data.std()) if not col_data.isnull().all() else None
            })
        elif col_data.dtype == 'object':
            # For string columns, get top values
            top_values = col_data.value_counts().head(5).to_dict()
            col_stats['top_values'] = {str(k): int(v) for k, v in top_values.items()}
        
        stats[column] = col_stats
    
    return stats


def get_schema_info(df):
    """
    Get schema information for the dataset
    """
    schema = {
        'columns': [],
        'total_columns': len(df.columns),
        'total_rows': len(df)
    }
    
    for column in df.columns:
        col_info = {
            'name': column,
            'dtype': str(df[column].dtype),
            'sample_values': df[column].dropna().head(3).tolist()
        }
        schema['columns'].append(col_info)
    
    return schema


def generate_quality_report(dataset):
    """
    Generate a detailed quality report for a dataset
    """
    try:
        df = load_dataset_data(dataset)
        
        if df is None:
            return None
            
        report = {
            'dataset_name': dataset.name,
            'generated_at': pd.Timestamp.now().isoformat(),
            'overall_quality_score': float(dataset.quality_score),
            'summary': {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': int(df.isnull().sum().sum()),
                'duplicate_rows': int(df.duplicated().sum())
            },
            'column_details': get_column_statistics(df),
            'recommendations': generate_recommendations(df)
        }
        
        return report
        
    except Exception as e:
        print(f"Error generating quality report for {dataset.name}: {str(e)}")
        return None


def generate_recommendations(df):
    """
    Generate data quality recommendations based on the dataset
    """
    recommendations = []
    
    # Check for missing values
    missing_cols = df.columns[df.isnull().any()].tolist()
    if missing_cols:
        recommendations.append({
            'type': 'missing_values',
            'severity': 'medium',
            'message': f'Columns with missing values: {", ".join(missing_cols[:5])}',
            'description': 'Consider handling missing values through imputation or removal.'
        })
    
    # Check for duplicates
    if df.duplicated().any():
        dup_count = df.duplicated().sum()
        recommendations.append({
            'type': 'duplicates',
            'severity': 'high',
            'message': f'{dup_count} duplicate rows found',
            'description': 'Investigate and remove duplicate records to improve data quality.'
        })
    
    # Check for data type inconsistencies
    for column in df.columns:
        if df[column].dtype == 'object':
            # Check if numeric values are stored as strings
            numeric_like = df[column].str.isnumeric().sum()
            if numeric_like > 0 and numeric_like / len(df) > 0.5:
                recommendations.append({
                    'type': 'data_type',
                    'severity': 'medium',
                    'message': f'Column "{column}" may contain numeric data stored as strings',
                    'description': 'Consider converting to appropriate numeric data type.'
                })
    
    return recommendations