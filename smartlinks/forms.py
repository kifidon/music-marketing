from django import forms

from .models import Fan


class FanOptInForm(forms.ModelForm):
    """Email + name only; preferred platform is taken from the URL in the view."""

    class Meta:
        model = Fan
        fields = ("email", "name")
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "you@example.com",
                    "autocomplete": "email",
                }
            ),
            "name": forms.TextInput(
                attrs={"placeholder": "Your name", "autocomplete": "name"}
            ),
        }
