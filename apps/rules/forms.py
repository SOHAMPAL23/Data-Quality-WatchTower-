from django import forms
from .models import Rule, RuleTemplate

class RuleForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=RuleTemplate.objects.filter(is_active=True),
        required=False,
        help_text="Select a template to auto-fill the form"
    )
    
    class Meta:
        model = Rule
        fields = ['name', 'description', 'dataset', 'rule_type', 'dsl_expression', 'severity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dataset': forms.Select(attrs={'class': 'form-control'}),
            'rule_type': forms.Select(attrs={'class': 'form-control'}),
            'dsl_expression': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': r"Example: NOT_NULL('email') or UNIQUE('id') or IN_RANGE('age', 18, 65) or REGEX('email', r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')"}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_dsl_expression(self):
        dsl_expression = self.cleaned_data.get('dsl_expression')
        if dsl_expression:
            # Validate that the DSL expression contains at least one valid function
            if not any(func in dsl_expression for func in ['NOT_NULL', 'UNIQUE', 'IN_RANGE', 'FOREIGN_KEY', 'REGEX', 'LENGTH_RANGE']):
                raise forms.ValidationError("DSL expression must contain a valid function like NOT_NULL, UNIQUE, IN_RANGE, etc.")
        return dsl_expression

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order rule types by name
        self.fields['rule_type'].choices = sorted(Rule.RULE_TYPES, key=lambda x: x[1])
        
        # Add dataset queryset filtering if needed
        if 'dataset' in self.fields:
            self.fields['dataset'].queryset = self.fields['dataset'].queryset.order_by('name')

class RuleFromTemplateForm(forms.ModelForm):
    """Form for creating a rule from a template"""
    
    class Meta:
        model = Rule
        fields = ['name', 'description', 'dataset', 'severity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dataset': forms.Select(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }