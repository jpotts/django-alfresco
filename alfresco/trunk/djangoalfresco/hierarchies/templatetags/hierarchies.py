from django import template
from django.db import models
Category = models.get_model('hierarchies', 'category')
Hierarchy = models.get_model('hierarchies', 'hierarchy')

register = template.Library()

#
# Get Latest Posts (templatetag)
#
class GetCategory(template.Node):
    def __init__(self, slug, var_name):
        self.var_name = var_name
        self.slug = slug
  
    def render(self, context):
        category = Category.objects.get(slug=self.slug)
        context[self.var_name] = category
        return ''

@register.tag(name='get_category')
def get_category(parser, token):
    try:
        tag_name, slug, trash, varname = token.contents.split()
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    return GetCategory(slug, varname)


class GetTop(template.Node):
    def __init__(self, slug, var_name, limit=10):
        self.var_name = var_name
        self.slug = slug
        self.limit = limit
  
    def render(self, context):
        category = Category.objects.get(slug=self.slug)
        object_list = category.get_top_content()
        context[self.var_name] = object_list
        return ''
    
@register.tag(name='get_top_stories')
def get_top_stories(parser, token):
    """
    For a given categories, it will return the top stories selected by the admin
    
    usage::
        {% get_top_stories [slug] [limit] as [var name] %}
        or {% get_top_stories [slug] as [var name] %}
    
    """
    bits = token.contents.split()
    
    limit = 10
    if len(bits) not in [4,5]:
        raise template.TemplateSyntaxError, "%s tag requires 4 or 5 arguments" % token.contents.split()[0]
    
    if len(bits) == 5:
        limit = bits[2]
    
    return GetTop(bits[1], bits[-1], limit)

class GetHierarchies(template.Node):
    def __init__(self,var_name):
        self.var_name = var_name
  
    def render(self, context):
        object_list = Hierarchy.objects.all()
        context[self.var_name] = object_list
        return ''

@register.tag
def get_hierarchies(parser, token):
    """
    Gets a list of all the hierarchies
    
    usage::
        {% get_hierarchies as [var name] %}
    
    """
    bits = token.contents.split()
    if len(bits) is not 3:
        raise template.TemplateSyntaxError, "%s tag requires 3 arguements" % token.contents.split()[0]
    if bits[1] != 'as':
        raise template.TemplateSyntaxError, "%s tag requires the second arguement to be 'as'" % token.contents.split()[0]
    return GetHierarchies(bits[2])
    
    
    
class GetTopCategories(template.Node):
    def __init__(self,hierarchy,var_name,*args):
        self.hierarchy = hierarchy
        self.var_name = var_name 
        self.exclude = []
        if args:
            self.exclude = args[0]   
  
    def render(self, context):            
        parent = Hierarchy.objects.get(name=self.hierarchy)
        if parent:           
            child_cats = Category.objects.filter(parent=None,hierarchy=parent)
            for ex in self.exclude:
                child_cats = child_cats.exclude(slug=ex)
            context[self.var_name] = child_cats
          
        return ''
    
@register.tag(name='get_top_categories')
def get_top_categories(parser, token):
    """
    Gets a list of all the top level categories for a given hierarchy.  
       [excluded] is an optional argument allowing user to pass in the slug of categories to be excluded from list.
    
    usage::
        {% get_top_categories [hierarchy] as [var name] [excluded1], [excluded2], ...%}
        or
        {% get_top_categories [hierarchy] as [var name] %}
    
    """
    bits = token.contents.split()    
    
    if len(bits) <= 3:
        raise template.TemplateSyntaxError, "%s tag requires at least 3 arguments " % token.contents.split()[0]
    if bits[2] != 'as':
        raise template.TemplateSyntaxError, "%s tag requires the the third argument to be 'as'" % token.contents.split()[0]
       
    return GetTopCategories(bits[1],bits[3],bits[4:]) 