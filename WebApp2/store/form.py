import imp
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Category

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=250, help_text='eg. youremail@gmail.com')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=50, required=True)
    name = forms.CharField(max_length=20, required=True)
    from_email = forms.CharField(max_length=50, required=True)
    message = forms.CharField(
        max_length=50, 
        widget=forms.Textarea(),
        help_text='Provide your message here!'
        )
    

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'slug', 'description', 'category', 'price', 'image', 'stock', 'available')


        
    # name = forms.CharField(max_length=250, required=True)
    # slug = forms.SlugField(max_length=250, required=True)
    # description = forms.Textarea()
    # category = forms.CharField(max_length=100, required=True)
    # price = forms.DecimalField(max_digits=10, decimal_places=2)
    # image = forms.ImageField()
    # stock = forms.IntegerField()
    # available = forms.BooleanField()
    # created = forms.DateTimeField()
    # updated = forms.DateTimeField()
    