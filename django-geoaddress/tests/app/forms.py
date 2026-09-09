"""Forms for tests.app."""

from django import forms

from .models import Location, LocationReadonly


class LocationForm(forms.ModelForm):
    """Form for Location model."""

    class Meta:
        model = Location
        fields = ["name", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter location name"}),
        }


class LocationReadonlyForm(forms.ModelForm):
    """Disable address once it has been set so the widget can render the layout."""

    class Meta:
        model = LocationReadonly
        fields = ["name", "address"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.address:
            self.fields["address"].disabled = True
            self.fields["address"].widget.attrs["readonly"] = True
