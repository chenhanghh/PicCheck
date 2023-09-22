from django import forms
from common.models import File
from projects.widgets import MultiFileInput


class FileFieldForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file']
        widgets = {
            'file': MultiFileInput(),
        }
