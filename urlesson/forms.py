from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.forms.widgets import DateInput
from .models import CustomUser, LessonRequest
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm
from django import forms
from .models import TeacherAvailability
from django.db import models
from django import forms
from .models import Teacher, Student

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    date_of_birth = forms.DateField(
        widget=DateInput(
            attrs={'type': 'date', 'class': 'w-full px-3 py-2 rounded bg-white text-black'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2', 'role', 'first_name', 'last_name', 'date_of_birth', 'can_commute', 'city', 'gender')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-3 py-2 rounded text-black'})

class TeacherExtraForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['price_per_minute_individual', 'price_per_minute_group', 'extra_student_group_minute_price', 'recurring_discount_percent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-3 py-2 rounded text-black'})

class StudentExtraForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['school', 'number_class']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-3 py-2 rounded text-black'})
            
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
        for field in ['price_per_minute_individual', 'price_per_minute_group', 'extra_student_group_minute_price']:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                self.add_error(field, "Price must be greater than or equal to 0.")

    class Meta:
        model = Teacher
        fields = [
            'price_per_minute_individual',
            'price_per_minute_group',
            'extra_student_group_minute_price',
        ]
        widgets = {
            'price_per_minute_individual': forms.NumberInput(attrs={'step': '0.01'}),
            'price_per_minute_group': forms.NumberInput(attrs={'step': '0.01'}),
            'extra_student_group_minute_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

class LessonRequestForm(forms.ModelForm):
    class Meta:
        model = LessonRequest
        fields = ['date', 'duration_minutes', 'time', 'is_group', 'repeat_weeks']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'repeat_weeks': forms.NumberInput(attrs={'min': 1, 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['repeat_weeks'].label = "Number of weekly lessons"
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'px-3 py-2 rounded text-black',
            })


class TeacherAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TeacherAvailability
        fields = ['day', 'start_time', 'end_time']
