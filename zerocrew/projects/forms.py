from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'outline']
        widgets = {
            'title':forms.TextInput(attrs={'placeholder':'プロジェクトのタイトルを入力', 'class':'form-control'}),
            'outline':forms.Textarea(attrs={'placeholder':'プロジェクトの概要や目的、求めるスキルなどを具体的に記述してください。', 'class':'form-control', 'rows': 8}),
        }
        labels = {
            'title':'プロジェクト名',
            'outline':'プロジェクト概要',
        }