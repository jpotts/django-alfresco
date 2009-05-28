from django.shortcuts import render_to_response,get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.urlresolvers import reverse
from django.utils.http import urlquote

from alfresco import utils
from alfresco.models import Content
from alfresco.decorators import ticket_required
from alfresco import service
from alfresco.forms import LoginForm, ContentSubmissionForm, SearchForm, CacheForm
from alfresco.settings import ALFRESCO_CONTENT_SUB_URL, ALFRESCO_EXCEPTION_CODES
from alfresco.service import generic_search
from alfresco.cache import image_cache
from alfresco.paginator import AlfrescoSearchPaginator

from hierarchies.models import Category, Hierarchy
from hierarchies import forms
from hierarchies.views import make_get_urls

import re

def get_category_templates(category):
        """
        Used by the layout congfig mostly
        Example the-paper/technology
        
        ['categories/the-paper/technology/detail.html',
         'categories/the-paper/detail.html'
         'categories/detail.html']
        
        """
        base = 'optaros/categories/%s' % category.slug_path
        bits = base.split('/')
        templates = []
        rng = range(1, len(bits)+1)
        rng.reverse()
        for num in rng:
            templates.append('/'.join(bits[:num]) + '/detail.html')
        return templates

@ticket_required
def category_detail(request, path, **kwargs):
    cat = get_object_or_404(Category, slug_path=path)
    ticket = request.user.ticket
    recent_docs = []
    if cat.space:
        recent_docs = cat.space.contents.filter(limit=20, order_by='-modified', alf_ticket=ticket)
    return render_to_response(get_category_templates(cat), {'recent_docs': recent_docs,
                                              'category': cat},context_instance=RequestContext(request) )
    
@ticket_required
def category_content_detail(request, path, id):
    """
    Category dependent view of a piece of alfresco content
    
    Allows for news/the-paper/taking-root/content/cd496430-a789-11dd-943d-7dc58b4e9440/
    """
    category = get_object_or_404(Category, slug_path=path)
    ticket = request.user.ticket
    try:
        content = category.space.contents.get(id=id, alf_ticket=ticket)
    except Content.DoesNotExist:
        raise Http404
    return render_to_response('optaros/categories/content_detail.html', 
                              {'category': category,
                                'object': content},
                              context_instance=RequestContext(request))

@ticket_required
def category_index(request, path):
    """
    The Content Browser.
    
    --Usage:
        Paginate
        TODO: Sort
    """
    category = get_object_or_404(Category, slug_path=path)
    ticket = request.user.ticket
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    order_by = request.GET.get('order_by', '-modified')
    
    paginator = category.space.contents.paginate(alf_ticket=ticket, \
                                             order_by=order_by, page=page, page_size=page_size)
    
    return render_to_response('optaros/categories/index.html', 
                              {'page' : paginator.page,
                               'pages' : paginator.pages(),
                               'category': category,
                               'order_by': order_by,
                               'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by)}, 
                                context_instance=RequestContext(request))


def get_hierarchy_templates(hierarchy):
    """
    Used by the layout congfig mostly
    ['hierarchies/news/detail.html',
     'hierarchies/detail.html']
    """
    return ['optaros/hierarchies/%s/detail.html' % hierarchy.slug, 'optaros/hierarchies/detail.html']

@ticket_required
def hierarchy_detail(request, slug, **kwargs):
    hierarchy = get_object_or_404(Hierarchy, slug=slug)
    recent_docs = []
    space = hierarchy.space
    if space:
        recent_docs = generic_search(space.q_path_any_below_include(), '-modified', 20, request.user.ticket, True)
    return render_to_response(get_hierarchy_templates(hierarchy), 
                              {'hierarchy': hierarchy, 
                               'categories':hierarchy.categories.filter(parent=None), 
                               'recent_docs' :recent_docs}
                              ,context_instance=RequestContext(request) )

def external_category_recent_documents(request, path):
    try:
        cat_or_hier = get_object_or_404(Hierarchy, slug=path)
    except:
        cat_or_hier = get_object_or_404(Category, slug_path=path)
    limit = int(request.GET.get('limit', 10))
    order_by = request.GET.get('order_by', '-modified')
    ticket = utils.get_external_user_ticket()
    recent_docs = []
    if cat_or_hier.space:
        q = "PATH:\"" + cat_or_hier.space.qname +"//*\" AND PATH:\"//cm:Published//*\""
        recent_docs = generic_search(q, order_by, limit, ticket, True)
    return render_to_response('hierarchies/recent_docs.html', 
                              {'recent_docs' :recent_docs}
                              ,context_instance=RequestContext(request))

@ticket_required
def home(request):
    return render_to_response('home.html', context_instance=RequestContext(request))

@ticket_required
def content(request, id):
    ticket = request.user.ticket
    content = Content.objects.get(id=id, alf_ticket=ticket)
    
    return render_to_response('optaros/detail.html', 
                {'object' :content },   
                context_instance=RequestContext(request))
@ticket_required
def print_view(request, id):
    ticket = request.user.ticket
    content = Content.objects.get(id=id, alf_ticket=ticket)
    
    return render_to_response('optaros/print_view.html', 
                {'object' :content },   
                context_instance=RequestContext(request))
      
@ticket_required
def static_content(request, id):
    ticket = request.user.ticket
    content = Content.objects.get(id=id, alf_ticket=ticket)
    return render_to_response('optaros/sc_detail.html', 
                {'object' :content },   
                context_instance=RequestContext(request))

def photo(request, path):
    """
    This is the pass through for images inserted into html via the Alfresco GUI
    """
    ticket = request.user.ticket
    if path.find('.') is -1:
        ss = service.SpaceStore(ticket, id=path)
    else:
        ss = service.SpaceStore(ticket, path=path)
    url = ss.get()
    return HttpResponseRedirect(url)

def create_search_string(get={}):
    values = []
    for key, value in get.items():
        if not value or key in ['page', 'order_by', 'page_size']:
            continue
        if key == 'q':
            if value.startswith('TEXT'):
                values.append(value)
            else:
                values.append('TEXT:%s' % value)
        else:
            values.append(value)
    return ' AND '.join(values).replace(' ', '%20')

def create_tag_search_string(get={}):
    values = []
    for key, value in get.items():
        if not value or key in ['page', 'order_by', 'page_size']:
            continue
        if key == 'q':
            if value.startswith('PATH'):
                values.append(value)
            else:                    
                values.append('PATH:"/cm:taggable/cm:%s/member"' % value)
        else:
            values.append(value)
    return ' AND '.join(values).replace(' ', '%20')

def clean_q(params):
    """
    This keeps the form and the pagination working.
    """
    name_re = re.compile('^@\\\{.*\}(?P<name>.*?):.*$')
    q_re = re.compile('TEXT:(?P<name>\w+)')
    params = params.copy()
    if params.has_key('q') and params['q'].startswith('TEXT'):
        name_list = params['q'].split(' AND ')
        for name in name_list:
            match = name_re.match(name)
            if match:
                params[match.groups()[0]] = name
        params['q'] = q_re.match(params['q']).groups()[0]
    return params

@ticket_required
def search(request):
    """
    Alfresco Advanced Search.
    """
    # Get pagination and sorting stuff
    page = request.GET.get('page',1)
    page_size = int(request.GET.get('page_size', 10))
    order_by = request.GET.get('order_by', 'title')
    
    # Make the search term
    search_term = create_search_string(request.GET)
    
    #Search
    paginator = AlfrescoSearchPaginator(q=search_term, order_by=order_by, page=page, page_size=page_size, alf_ticket=request.user.ticket)

    #Search Form
    form = SearchForm(initial=clean_q(request.GET))
    
    return render_to_response('optaros/search.html',
            {'page' : paginator.page,
             'pages': paginator.pages(),
             'search_term': search_term,
             'order_by' : order_by,
             'form' : form,
             'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by, q=search_term)}, 
             context_instance=RequestContext(request))
    
@ticket_required
def tag_search(request):
    """
    Alfresco Tag Search.
    """
    # Get pagination and sorting stuff
    page = request.GET.get('page',1)
    page_size = int(request.GET.get('page_size', 10))
    order_by = request.GET.get('order_by', 'title')
    query = request.GET.get('q')
     
    # Make the search term
    search_term = create_tag_search_string(request.GET)
        
    #Search
    paginator = AlfrescoSearchPaginator(q=search_term, order_by=order_by, page=page, page_size=page_size, alf_ticket=request.user.ticket)

    #Search Form
    form = SearchForm(initial=clean_q(request.GET))
    
    return render_to_response('optaros/tag_search.html',
            {'page' : paginator.page,
             'pages': paginator.pages(),
             'search_term': search_term,
             'query': query,
             'order_by' : order_by,
             'form' : form,
             'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by, q=search_term)}, 
             context_instance=RequestContext(request))    

    
    