from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, Teacher, Student
from django.forms.widgets import DateInput

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

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