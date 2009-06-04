#
# Copyright 2009 Optaros, Inc.
#
from hierarchies.models import Hierarchy, Category
from django.contrib import admin
from django import forms

class HierarchyAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Hierarchy, HierarchyAdmin)
    

class CategoryAdminForm(forms.ModelForm):
    def clean_hierarchy(self):
        if not self.data['hierarchy'] and not self.data['parent']:
            raise forms.ValidationError("A hierarchy is required if no parent is given.")
        return self.cleaned_data['hierarchy']
    
    def clean_parent(self):
        if not self.data['parent'] and not self.data['hierarchy']:
            raise forms.ValidationError("A parent is required if no hierarchy is given.")
        return self.cleaned_data['parent']

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    
    form = CategoryAdminForm
    ordering = ['slug_path']
    
admin.site.register(Category, CategoryAdmin)