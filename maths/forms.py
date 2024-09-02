from django import forms
from .models import MathProblem

class MathProblemForm(forms.ModelForm):
    class Meta:
        model = MathProblem
        fields = ['topic', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
