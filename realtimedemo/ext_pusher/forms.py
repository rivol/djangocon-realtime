from django import forms


class PusherForm(forms.Form):
    message = forms.CharField(max_length=200)
