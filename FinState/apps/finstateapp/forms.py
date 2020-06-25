from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']


class UploadFileForm(forms.Form):
    file = forms.FileField()


class HoldingRegistrationForm(forms.Form):
    name = forms.CharField(label='Name of holding', max_length=100)

    class Meta:
        fields = ['name']


class FactoryRegistrationForm(forms.Form):
    name = forms.CharField(label='Name of factory', max_length=100)
    symbol = forms.CharField(label='Name of factory', max_length=10)
    requisites = forms.CharField(label='Requisites', max_length=100)
    phone = forms.CharField(label='Contact telephone number', max_length=100)
    file = forms.FileField(label='File in excel format')

    class Meta:
        fields = ['name', 'symbol', 'requisites', 'phone', 'file']


class DateForm(forms.Form):
    start_date = forms.DateField(input_formats='%Y,%m,%d', widget=forms.SelectDateWidget())
    end_date = forms.DateField(input_formats='%Y,%m,%d', widget=forms.SelectDateWidget())

    class Meta:
        fields = ['start_date', 'end_date']
