from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import Chore, Household, User


class SignUpForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    household_name = forms.CharField(max_length=150)

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


class JoinHouseholdForm(forms.Form):
    invite_code = forms.CharField(max_length=64)


class MemberForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ["name"]


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = [
            "name",
            "description",
            "assignee",
            "due_date",
            "priority",
            "category",
            "status",
            "recurrence",
            "is_recurring",
			"rotation_enabled",
        ]

    def __init__(self, *args, household, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = User.objects.filter(household=household)
