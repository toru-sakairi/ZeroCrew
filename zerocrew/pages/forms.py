from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ('category', 'content', 'url')
        widgets = {
            'url':forms.HiddenInput(),
        }
        
        