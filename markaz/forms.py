from django import forms
from .models import Student, Teacher, Group

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'phone', 'group', 'balance']

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['name','user', 'phone']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'


from django import forms
from django.contrib.auth.models import User
from .models import Teacher, Group

class SimpleTeacherForm(forms.Form):
    first_name = forms.CharField(label="Ism", widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label="Login (User)", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Parol", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label="Telefon", widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Guruh tanlash qismi
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(), 
        label="Guruh biriktirish",
        empty_label="Guruhni tanlang",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )