from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class RegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = UserProfile
        fields = ['email', 'phone']

    def save(self, commit=True):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        email = self.cleaned_data['email']
        user = User.objects.create_user(username=username, password=password, email=email)
        user_profile = super().save(commit=False)
        user_profile.user = user
        if commit:
            user_profile.save()
        return user_profile
    
class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate username from the User model
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username

    def clean_username(self):
        username = self.cleaned_data['username']
        # Check if the username is already taken by another user
        if User.objects.exclude(id=self.instance.user.id).filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
    

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CheckoutForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea)
    phone = forms.CharField(max_length=15)