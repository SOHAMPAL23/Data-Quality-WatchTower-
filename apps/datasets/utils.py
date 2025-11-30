import pandas as pd
import numpy as np
from typing import List, Dict, Any
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def analyze_dataset_for_rules(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Analyze a dataset and generate rule recommendations based on the data.
    
    Args:
        df: Pandas DataFrame containing the dataset
        
    Returns:
        List of rule recommendations with confidence scores
    """
    recommendations = []
    
    for column in df.columns:
        try:
            series = df[column]
            
            # Skip empty columns
            if len(series.dropna()) == 0:
                continue
            
            # NOT_NULL rule recommendation
            null_percentage = series.isnull().sum() / len(series) * 100
            if null_percentage < 95:  # Recommend NOT_NULL if less than 95% are null
                confidence = min(100, int(100 - null_percentage))
                recommendations.append({
                    'type': 'NOT_NULL',
                    'column': column,
                    'confidence': confidence,
                    'reason': f'{null_percentage:.1f}% of values are null',
                    'severity': 'HIGH' if null_percentage < 10 else 'MEDIUM' if null_percentage < 50 else 'LOW'
                })
            
            # UNIQUE rule recommendation
            non_null_series = series.dropna()
            if len(non_null_series) > 0:
                unique_percentage = series.nunique() / len(non_null_series) * 100
                if unique_percentage > 90:  # Recommend UNIQUE if more than 90% are unique
                    confidence = min(100, int(unique_percentage))
                    recommendations.append({
                        'type': 'UNIQUE',
                        'column': column,
                        'confidence': confidence,
                        'reason': f'{unique_percentage:.1f}% of non-null values are unique',
                        'severity': 'HIGH' if unique_percentage > 95 else 'MEDIUM'
                    })
            
            # IN_RANGE rule recommendation for numeric columns
            if pd.api.types.is_numeric_dtype(series):
                non_null_series = series.dropna()
                if len(non_null_series) > 0:
                    min_val = non_null_series.min()
                    max_val = non_null_series.max()
                    
                    # Check if values are within a reasonable range
                    if min_val >= 0 and max_val <= 1000000:  # Arbitrary reasonable range
                        confidence = 80
                        recommendations.append({
                            'type': 'IN_RANGE',
                            'column': column,
                            'confidence': confidence,
                            'reason': f'Numeric values range from {min_val} to {max_val}',
                            'params': {
                                'min': float(min_val),
                                'max': float(max_val)
                            },
                            'severity': 'MEDIUM'
                        })
            
            # REGEX rule recommendations for string columns
            if pd.api.types.is_string_dtype(series) or series.dtype == 'object':
                non_null_series = series.dropna()
                if len(non_null_series) > 0:
                    # Convert to string to ensure consistent processing
                    str_series = non_null_series.astype(str)
                    
                    # Check for email-like patterns
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    email_matches = str_series.str.contains(email_pattern, na=False, regex=True).sum()
                    email_percentage = email_matches / len(str_series) * 100
                    if email_percentage > 50:  # Recommend REGEX for emails if more than 50% match
                        confidence = min(100, int(email_percentage))
                        recommendations.append({
                            'type': 'REGEX',
                            'column': column,
                            'confidence': confidence,
                            'reason': f'{email_percentage:.1f}% of values look like email addresses',
                            'params': {
                                'pattern': email_pattern
                            },
                            'severity': 'HIGH' if email_percentage > 80 else 'MEDIUM'
                        })
                    
                    # Check for phone number patterns
                    phone_pattern = r'^(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
                    phone_matches = str_series.str.contains(phone_pattern, na=False, regex=True).sum()
                    phone_percentage = phone_matches / len(str_series) * 100
                    if phone_percentage > 50:  # Recommend REGEX for phones if more than 50% match
                        confidence = min(100, int(phone_percentage))
                        recommendations.append({
                            'type': 'REGEX',
                            'column': column,
                            'confidence': confidence,
                            'reason': f'{phone_percentage:.1f}% of values look like phone numbers',
                            'params': {
                                'pattern': phone_pattern
                            },
                            'severity': 'MEDIUM'
                        })
                    
                    # Check for URL patterns
                    url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
                    url_matches = str_series.str.contains(url_pattern, na=False, regex=True).sum()
                    url_percentage = url_matches / len(str_series) * 100
                    if url_percentage > 30:  # Recommend REGEX for URLs if more than 30% match
                        confidence = min(100, int(url_percentage))
                        recommendations.append({
                            'type': 'REGEX',
                            'column': column,
                            'confidence': confidence,
                            'reason': f'{url_percentage:.1f}% of values look like URLs',
                            'params': {
                                'pattern': url_pattern
                            },
                            'severity': 'MEDIUM'
                        })
            
            # DATE validation for potential date columns
            if pd.api.types.is_string_dtype(series) or series.dtype == 'object':
                non_null_series = series.dropna()
                if len(non_null_series) > 0:
                    # Try to parse as dates
                    date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']
                    parsed_successfully = 0
                    
                    for fmt in date_formats:
                        try:
                            pd.to_datetime(non_null_series.head(100), format=fmt, errors='raise')
                            parsed_successfully += 1
                        except (ValueError, TypeError):
                            continue
                    
                    if parsed_successfully > 0:
                        confidence = min(100, int((parsed_successfully / len(date_formats)) * 100))
                        recommendations.append({
                            'type': 'DATE_FORMAT',
                            'column': column,
                            'confidence': confidence,
                            'reason': f'Values appear to be dates in common formats',
                            'params': {
                                'formats': date_formats
                            },
                            'severity': 'MEDIUM'
                        })
            
            # Length validation for string columns
            if pd.api.types.is_string_dtype(series) or series.dtype == 'object':
                non_null_series = series.dropna()
                if len(non_null_series) > 0:
                    # Calculate lengths
                    lengths = non_null_series.astype(str).str.len()
                    min_len = lengths.min()
                    max_len = lengths.max()
                    
                    # If there's significant variation in length, suggest length bounds
                    if max_len - min_len > 10 and max_len <= 1000:  # Reasonable upper bound
                        confidence = 70
                        recommendations.append({
                            'type': 'LENGTH_RANGE',
                            'column': column,
                            'confidence': confidence,
                            'reason': f'String lengths vary from {min_len} to {max_len} characters',
                            'params': {
                                'min_length': int(min_len),
                                'max_length': int(max_len)
                            },
                            'severity': 'LOW'
                        })
                        
        except Exception as e:
            logger.warning(f"Error analyzing column {column}: {str(e)}")
            continue
    
    return recommendations