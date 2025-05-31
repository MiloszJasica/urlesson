from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.forms.widgets import DateInput
from .models import CustomUser, LessonRequest
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm



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
    def clean_username(self):
        email = self.cleaned_data.get('username')

        if not email:
            raise forms.ValidationError("It's not e-mail.")
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Incorrect e-mail.")

        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("User doesn't exist.")

        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if not password:
            return cleaned_data

        user = authenticate(username=email, password=password)
        if user is None:
            raise forms.ValidationError("Incorrect password.")

        self.user_cache = user
        return cleaned_data




class TeacherPricingForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        for field in self.fields:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                self.add_error(field, "Price must be higher than 0.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 rounded text-black',
            })

    class Meta:
        model = CustomUser
        fields = [
            'lesson_price_45min',
            'lesson_price_60min',
            'group_lesson_base_price',
            'group_price_per_additional_student',
        ]
        widgets = {
            'lesson_price_45min': forms.NumberInput(attrs={'step': '1.0'}),
            'lesson_price_60min': forms.NumberInput(attrs={'step': '1.0'}),
            'group_lesson_base_price': forms.NumberInput(attrs={'step': '1.0'}),
            'group_price_per_additional_student': forms.NumberInput(attrs={'step': '1.0'}),
        }


class LessonRequestForm(forms.ModelForm):
    class Meta:
        model = LessonRequest
        fields = ['date', 'time', 'duration_minutes', 'is_group', 'students']

    students = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='student'),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 rounded text-black',
            })