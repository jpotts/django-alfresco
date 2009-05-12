from alfresco import utils
from alfresco.models import Content, StaticContent
from alfresco.service import get_navigation_ul, AlfrescoException
from alfresco.template import AlfrescoTemplateNode

from django import template
from django.template import Variable, Template

import re


register = template.Library()

def mask_image_tags(value):
    d = re.compile('alfresco[^}]*SpacesStore')
    return d.sub('alfresco/images', value)

register.filter(mask_image_tags)

class GetNavigation(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        try:
            user = Variable('user').resolve(context)
            nav = get_navigation_ul(user.ticket)
            return nav
        
        except (template.VariableDoesNotExist, AlfrescoException):
            return ''

@register.tag(name="get_navigation")
def get_navigation(parser, token):
    return GetNavigation()
    
class GetContent(AlfrescoTemplateNode):
    """
    For a given content slug, it will display a static block of html
    usage::
        {% get_content [slug] %}
    
    """
    def __init__(self, slug):
        self.slug = slug
    
    def deliver(self, context):  
        try:
            user = Variable('user').resolve(context)
            sc_item = StaticContent.objects.get(slug=self.slug)
            content = Content.objects.get(id=sc_item.doc_id, alf_ticket=user.ticket)
           
            return Template(content.content).render({})  
        
        except (template.VariableDoesNotExist, Content.DoesNotExist, StaticContent.DoesNotExist, UnicodeDecodeError):
            return ''

@register.tag(name="get_content")
def get_content(parser, token):
    bits = token.contents.split() 
    
    if len(bits) is not 2:
        raise template.TemplateSyntaxError, "%s tag requires only 2 arguments" % token.contents.split()[0]   
    
    return GetContent(bits[1])