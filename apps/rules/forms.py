from django import forms
from .models import Rule, RuleTemplate
from apps.datasets.models import Dataset


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


class RuleFromTemplateForm(forms.ModelForm):
    """Form for creating a rule from a template"""
    
    # Template-specific fields
    column_name = forms.CharField(
        max_length=100,
        required=False,
        help_text="Column name to apply the rule to"
    )
    
    min_value = forms.FloatField(
        required=False,
        help_text="Minimum value for range checks"
    )
    
    max_value = forms.FloatField(
        required=False,
        help_text="Maximum value for range checks"
    )
    
    min_length = forms.IntegerField(
        required=False,
        help_text="Minimum length for text fields"
    )
    
    max_length = forms.IntegerField(
        required=False,
        help_text="Maximum length for text fields"
    )
    
    pattern = forms.CharField(
        max_length=255,
        required=False,
        help_text="Regex pattern for validation"
    )
    
    class Meta:
        model = Rule
        fields = ['name', 'description', 'dataset', 'severity']
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'dataset': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, template=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.template = template
        self.user = user
        
        if user:
            # Filter datasets by user's ownership
            self.fields['dataset'].queryset = Dataset.objects.filter(owner=user, is_active=True)
        
        if template:
            # Customize form based on template type
            self._customize_form_for_template(template)
    
    def _customize_form_for_template(self, template):
        """Customize form fields based on template type"""
        if template.template_type == 'MISSING_VALUE':
            self.fields['column_name'].required = True
        elif template.template_type == 'DUPLICATE_DETECTION':
            self.fields['column_name'].required = True
        elif template.template_type == 'OUTLIER_DETECTION':
            self.fields['column_name'].required = True
            self.fields['min_value'].required = True
            self.fields['max_value'].required = True
        elif template.template_type == 'SCHEMA_VALIDATION':
            self.fields['column_name'].required = True
            self.fields['pattern'].required = True
        elif template.template_type == 'CUSTOM':
            # For custom templates, show all fields but make none required
            pass
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.template:
            # Validate template-specific fields
            if self.template.template_type == 'OUTLIER_DETECTION':
                min_val = cleaned_data.get('min_value')
                max_val = cleaned_data.get('max_value')
                if min_val is not None and max_val is not None and min_val >= max_val:
                    raise forms.ValidationError("Minimum value must be less than maximum value.")
        
        return cleaned_data
    
    def save(self, commit=True):
        rule = super().save(commit=False)
        
        # Generate DSL expression from template
        if self.template:
            dsl_params = {
                'column_name': self.cleaned_data.get('column_name', ''),
                'min_value': self.cleaned_data.get('min_value'),
                'max_value': self.cleaned_data.get('max_value'),
                'min_length': self.cleaned_data.get('min_length'),
                'max_length': self.cleaned_data.get('max_length'),
                'pattern': self.cleaned_data.get('pattern', ''),
            }
            
            # Format the DSL template with actual values
            try:
                rule.dsl_expression = self.template.dsl_template.format(**dsl_params)
            except KeyError as e:
                raise forms.ValidationError(f"Missing parameter for DSL template: {e}")
        
        if commit:
            rule.save()
        return rule