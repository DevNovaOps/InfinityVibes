import re
from django import forms
from django.contrib.auth.hashers import make_password
from .models import User, VendorProfile

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'})
    )


class UserSignupForm(forms.ModelForm):
    """
    Handles new user registration and manually hashes the password.
    """
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a strong password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'user_type']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'user_type': forms.HiddenInput(),
        }

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data["password"]
        user.password = make_password(raw_password)
        if commit:
            user.save()
        return user


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = [
            'business_name', 
            'service_category', 
            'experience', 
            'business_description'
        ]
        labels = {
            'business_name': 'Business Name',
            'service_category': 'Primary Service Offered',
            'experience': 'Years of Professional Experience',
            'business_description': 'Description of Your Business',
        }
        widgets = {
            'business_name': forms.TextInput(attrs={'placeholder': 'e.g., Creative Catering Co.'}),
            'service_category': forms.Select(),
            'experience': forms.Select(), 
            'business_description': forms.Textarea(attrs={'placeholder': 'Describe your services...', 'rows': 4}),
        }