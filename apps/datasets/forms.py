from django import forms
from .models import Dataset


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'description', 'source_type', 'file', 'table_name', 'db_connection']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'table_name': forms.TextInput(attrs={'class': 'form-control'}),
            'db_connection': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '{"host": "localhost", "port": 5432, "database": "mydb", "user": "myuser", "password": "mypassword"}'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['table_name'].required = False
        self.fields['db_connection'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type')
        file = cleaned_data.get('file')
        table_name = cleaned_data.get('table_name')
        db_connection = cleaned_data.get('db_connection')
        
        if source_type == 'CSV' and not file:
            raise forms.ValidationError("CSV file is required for CSV datasets.")
            
        if source_type == 'DB':
            if not table_name:
                raise forms.ValidationError("Table name is required for database datasets.")
            if not db_connection:
                raise forms.ValidationError("Database connection details are required for database datasets.")
                
        return cleaned_data