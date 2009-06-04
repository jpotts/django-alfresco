#
# Copyright 2009 Optaros, Inc.
#
from django import forms
from alfresco import utils
from django.contrib.auth import authenticate

class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(max_length=50, widget=forms.widgets.PasswordInput())
    next = forms.CharField(max_length=200, widget=forms.HiddenInput)
    
    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Please enter a correct username and password. Note that both fields are case-sensitive.")
            elif not self.user_cache.is_active:
                raise forms.ValidationError("This account is inactive.")
            
        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class ContentSubmissionForm(forms.Form):
    title  = forms.CharField(max_length=100)
    author = forms.CharField(max_length=100)
    date = forms.DateField()
    body = forms.CharField(max_length=10000, widget=forms.widgets.Textarea())
    folderId = forms.CharField(max_length=50, widget=forms.widgets.HiddenInput())

class SearchForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', [])
        self.base_fields['q'] = forms.CharField(label="Key Words", max_length=100)
        super(SearchForm, self).__init__(*args, **kwargs)
        

class CacheForm(forms.Form):
    """
    Used to clear cache elements
    """
    
    def __init__(self, *args, **kwargs):
        cache = kwargs.pop('cache', None)
        if cache:
            self.base_fields.clear()
            for key in cache._cache.keys():
                self.base_fields[key] = forms.BooleanField(required=False)
        super(CacheForm, self).__init__(*args, **kwargs)