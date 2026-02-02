"""Program forms."""
from django import forms

from apps.auth_app.models import User

from .models import Program, UserProgramRole


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["name", "description", "colour_hex", "status"]
        widgets = {
            "colour_hex": forms.TextInput(attrs={"type": "color"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class UserProgramRoleForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True))
    role = forms.ChoiceField(choices=UserProgramRole.ROLE_CHOICES)

    def __init__(self, *args, program=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = program
