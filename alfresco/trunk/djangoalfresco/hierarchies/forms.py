#
# Copyright 2009 Optaros, Inc.
#
from django import forms
from xml.dom import minidom 
class Document(object):
    def __init__(self, seq, org):
        self.seq = seq
        self.org = minidom.parseString(org)
        self.xml = minidom.Document()
        self.objects = self.xml.createElement('django-objects')
        self.objects.setAttribute('version', "1")
        self.xml.appendChild(self.objects)
        
    def clean(self):
        for s in self.seq:  
            for elem in self.org.getElementsByTagName('object'):
                if elem.attributes['pk'].value == s:
                    self.objects.appendChild(elem)
    def to_xml(self):
        self.clean()
        return self.xml.toxml()

class OrderingForm(forms.Form):
    sequence = forms.CharField(max_length=1024, widget=forms.widgets.HiddenInput(), required=False)
    
    def save(self, category, xml):
        clean = lambda x: x.replace('top[]=','').split('&')
        # This should be cleaned_data, but for some reason errors get tossed.
        # TODO: Fix this
        seq = self.data['sequence']
        if seq:
            seq = clean(seq)
        else:
            seq = []        
        doc = Document(seq, xml)
        category.set_top_content(doc.to_xml())