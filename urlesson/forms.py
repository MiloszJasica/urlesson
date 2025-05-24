from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.forms.widgets import DateInput
from .models import CustomUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 rounded text-black',
            })

class CustomUserExtraForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=DateInput(
            attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded bg-white text-black',
                'placeholder': 'dd-mm-yyyy'
            },
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'date_of_birth', 'can_commute', 'city')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 rounded text-black',
            })
            
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Email', widget=forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 rounded bg-white text-black'
    }))

    def clean_username(self):
        email = self.cleaned_data.get('username')
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Invalid email form.")
        return email

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not email:
            raise forms.ValidationError("Complete the email field.")
        if not password:
            raise forms.ValidationError("Complete the password field.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("User does not exist.")

        user = authenticate(username=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid password.")

        self.user_cache = user

        return self.cleaned_data


