# core/forms.py
from django import forms
from .models import Site, Asset,chat, Human_resource
from django.utils import timezone

class AIAssistantForm(forms.Form):
    query = forms.CharField(max_length=500, required=True, widget=forms.TextInput(attrs={'placeholder': 'Ask your question here...'}))


class SiteForm(forms.ModelForm):
    class Meta:                                                                                                                                              
        model = Site
        fields = ['name', 'location', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter site name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)
class HumanResourceForm(forms.ModelForm):
    class Meta:
        model = Human_resource                                                                                                                                                       
        fields = ['site', 'name', 'phone_number', 'role', 'start_date', 'end_date', 'salary']
        widgets = {
            'site': forms.Select(attrs={                                                                                                                                
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter employee name',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder':'Enter Emloyee Phone number(+2547123456789)',

            }),
            'role': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter job role',
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-input pl-7',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
            }),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)
    
        if user is not None:
           self.fields['site'].queryset = Site.objects.filter(owner=user)
        


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['site', 'name', 'type', 'units', 'serial_number', 
                  'quantity_in_stock', 'cost_per_unit', 'maintenance_date', 
                  'assignment_date', 'discription']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'units': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost_per_unit': forms.NumberInput(attrs={'class': 'form-control'}),
            'maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assignment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'discription': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields['site'].queryset = Site.objects.filter(owner=self.user)

    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        # Set initial date if creating a new asset
        if not kwargs.get('instance'):
            self.fields['assignment_date'].initial = timezone.now().date()
            
        # Make fields dynamically required or hidden based on asset type
        self.fields['serial_number'].required = False
        self.fields['quantity_in_stock'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        asset_type = cleaned_data.get('type')
        
        # Validate based on asset type
        if asset_type == 'equipment' and not cleaned_data.get('serial_number'):
            self.add_error('serial_number', 'Serial number is required for equipment.')
        elif asset_type == 'material' and cleaned_data.get('quantity_in_stock') is None:
            self.add_error('quantity_in_stock', 'Quantity is required for materials.')
        
        return cleaned_data