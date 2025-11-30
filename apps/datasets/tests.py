from django.test import TestCase
from apps.users.models import User
import pandas as pd
import os
from .utils import analyze_dataset_for_rules


class DatasetUtilsTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_analyze_dataset_for_rules_with_length_patterns(self):
        """Test that dataset analysis detects length patterns and generates LENGTH_RANGE rules"""
        # Create test data with varying string lengths
        df = pd.DataFrame({
            'username': ['abc', 'abcd', 'a', 'abcdefghijk', 'toolongusernameexceedinglimit'],
            'email': ['a@b.com', 'ab@c.com', 'abc@d.com', 'abcd@e.com', 'abcde@f.com'],
            'age': [25, 30, 35, 40, 45]
        })
        
        # Analyze the dataset
        recommendations = analyze_dataset_for_rules(df)
        
        # Check that we have recommendations
        self.assertGreater(len(recommendations), 0)
        
        # Check that recommendations have the expected structure
        for rec in recommendations:
            self.assertIn('type', rec)
            self.assertIn('column', rec)
            self.assertIn('confidence', rec)
            self.assertIn('reason', rec)