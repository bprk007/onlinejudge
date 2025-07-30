from django import forms
from submit.models import CodeSubmission

LANGUAGE_CHOICES = [
    ('python', 'Python'),
    ('cpp', 'C++'),
    ('java', 'Java'),
]



class CodeSubmissionForm(forms.ModelForm):
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES)

    class Meta:
        model = CodeSubmission
        fields = ["language", "code", "input_data"]


