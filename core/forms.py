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

class RefillForm(forms.Form):
    """
    Simple form to add balance to the user's wallet.
    """
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=1.00)
