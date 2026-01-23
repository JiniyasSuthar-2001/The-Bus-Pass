from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating a new user. 
    Extends the default UserCreationForm to use our CustomUser model.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Allow spaces but strip leading/trailing
        if username:
            username = username.strip()
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8 or len(password) > 20:
            raise forms.ValidationError("Password must be between 8 and 20 characters.")
        if not any(char.isupper() for char in password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
            raise forms.ValidationError("Password must contain at least one special symbol (@, #, $, etc.).")
        return password

class RefillForm(forms.Form):
    """
    Simple form to add balance to the user's wallet.
    """
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1.00)
