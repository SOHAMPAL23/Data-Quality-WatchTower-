from django import forms
from .models import Rule


class RuleForm(forms.ModelForm):
    class Meta:
        model = Rule
        fields = ['name', 'description', 'rule_type', 'dsl_expression']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rule_type': forms.Select(attrs={'class': 'form-select'}),
            'dsl_expression': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "Example: NOT_NULL('email') or UNIQUE('id') or IN_RANGE('age', 18, 65) or REGEX('email', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')"}),
        }
    
    def clean_dsl_expression(self):
        dsl_expression = self.cleaned_data.get('dsl_expression')
        rule_type = self.cleaned_data.get('rule_type')
        
        # Basic validation for DSL expression format
        if rule_type == 'NOT_NULL' and not dsl_expression.startswith('NOT_NULL('):
            raise forms.ValidationError("NOT_NULL rule must start with NOT_NULL('column_name')")
            
        if rule_type == 'UNIQUE' and not dsl_expression.startswith('UNIQUE('):
            raise forms.ValidationError("UNIQUE rule must start with UNIQUE('column_name')")
            
        if rule_type == 'IN_RANGE' and not dsl_expression.startswith('IN_RANGE('):
            raise forms.ValidationError("IN_RANGE rule must start with IN_RANGE('column_name', min, max)")
            
        if rule_type == 'FOREIGN_KEY' and not dsl_expression.startswith('FOREIGN_KEY('):
            raise forms.ValidationError("FOREIGN_KEY rule must start with FOREIGN_KEY('column_name', 'ref_table', 'ref_column')")
            
        if rule_type == 'REGEX' and not dsl_expression.startswith('REGEX('):
            raise forms.ValidationError("REGEX rule must start with REGEX('column_name', 'pattern')")
            
        return dsl_expression