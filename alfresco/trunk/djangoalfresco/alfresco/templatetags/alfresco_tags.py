from django.template import TemplateSyntaxError
from alfresco import utils
from alfresco.models import Content, StaticContent
from alfresco.service import get_navigation_ul, AlfrescoException, get_person
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
    
    def render(self, context):  
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

class FormatTags(template.Node):
    """
    For a given set of list-separated tags, format a linked list of the tags in the list
    usage::
        {% format_tags [tags] %}   
        
    """

    def __init__(self, tag_var):
        self.tag_var = tag_var
        
    def render(self, context):
        tag_list_csv = Variable(self.tag_var).resolve(context)
        
        if (tag_list_csv is None):
            return None
            
        tag_list = tag_list_csv.split(',')
            
        #markup = ""
        #for tag in tag_list:
        #    markup += '<a href="/blog-term/%s" name="blogtag">%s</a>' % (tag, tag)
            # what is the "has next" syntax in an iterator in python
        markup = ', '.join(['<a href="/sample_site/tag_search?q=%s" name="blogtag">%s</a>' % (tag, tag) for tag in tag_list])

        return markup
    
@register.tag(name="format_tags")
def format_tags(parser, token):
    bits = token.contents.split()
    
    if len(bits) is not 2:
        raise template.TemplateSyntaxError, "%s tag requires 2 arguments" % token.contents.split()[0]
    
    return FormatTags(bits[1])

class FormatUserLink(template.Node):
    """
    For a given username, format a mailto link that points to the user's email address as retrieved from Alfresco.
    usage::
        {% format_user_link [user_name] %}   
        
    """

    def __init__(self, user_name):
        self.user_name = user_name
        
    def render(self, context):
        user = Variable('user').resolve(context)
        user_name_string = Variable(self.user_name).resolve(context)
        try:
            user_props = get_person(user_name_string, user.ticket)
        except:
            user_props = None
        
        if (user_props is None):
            markup = user_name_string
        else:
            markup = '<a href="mailto:%s" name="user_link">%s %s</a>' % (user_props['email'], user_props['firstName'], user_props['lastName'])       
        
        return markup
    
@register.tag(name="format_user_link")
def format_user_link(parser, token):
    bits = token.contents.split()
    
    if len(bits) is not 2:
        raise template.TemplateSyntaxError, "%s tag requires 2 arguments" % token.contents.split()[0]
    
    return FormatUserLink(bits[1])