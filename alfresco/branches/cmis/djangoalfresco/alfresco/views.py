from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.urlresolvers import reverse

from alfresco.models import Content
from alfresco.decorators import ticket_required
from alfresco import service
from alfresco.forms import LoginForm, ContentSubmissionForm, SearchForm, CacheForm
from alfresco.settings import ALFRESCO_CONTENT_SUB_URL, ALFRESCO_EXCEPTION_CODES
from alfresco.cache import image_cache
from alfresco.paginator import AlfrescoSearchPaginator

import re

from hierarchies.views import make_get_urls

@ticket_required
def content(request, id):
    ticket = request.user.ticket
    content = Content.objects.get(id=id, alf_ticket=ticket)
    
    return render_to_response('alfresco/detail.html', 
                {'object' :content },   
                context_instance=RequestContext(request))
@ticket_required
def print_view(request, id):
    ticket = request.user.ticket
    content = Content.objects.get(id=id, alf_ticket=ticket)
    
    return render_to_response('alfresco/print_view.html', 
                {'object' :content },   
                context_instance=RequestContext(request))
      
@ticket_required
def static_content(request, id):
    ticket = request.user.ticket
    content = Content.objects.get(id=id, alf_ticket=ticket)
    return render_to_response('alfresco/sc_detail.html', 
                {'object' :content },   
                context_instance=RequestContext(request))
    
def login(request):
    """
    Makes a request to Alfresco and throws the alf_ticket in the users settings
    """
    if request.user.is_authenticated():
        auth_logout(request)
    
    if request.POST:
        form =  LoginForm(request.POST)
        if form.is_valid():
            auth_login(request, form.get_user()) 
            return HttpResponseRedirect(form.cleaned_data['next'])
    
    else:
        form =  LoginForm(initial={'next' :  request.GET.get('next', '/')})
    
    error_msg = request.GET.get('error', None)
    if error_msg:
        error_msg = ALFRESCO_EXCEPTION_CODES[int(error_msg)]

    return render_to_response('alfresco/login.html', 
                {'form' :form , 'error_msg' : error_msg},   
                context_instance=RequestContext(request))

def logout(request):
    """
    Makes a request to Alfresco and throws the alf_ticket in the users settings
    """
    try:
        # Let's not delete the ticket. No sense in doing such a thing, I'm pretty sure it just
        # f's with the model.
        #alf_user = request.user
        #alf_user.ticket = None
        #alf_user.save()
        auth_logout(request)
        #This is a dumb problem to have. You need to be a authenticated to delete a Ticket,
        #yet you can use the ticket you have to authenticate. So i guess we orphan tickets?
        #service.logout(request.session['alf_ticket'])
    except Exception, e:
        pass
        
    return render_to_response('alfresco/logout.html',
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
    
    return render_to_response('alfresco/search.html',
            {'page' : paginator.page,
             'pages': paginator.pages(),
             'search_term': search_term,
             'order_by' : order_by,
             'form' : form,
             'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by, q=search_term)}, 
             context_instance=RequestContext(request))

def content_submission(request, space_id):
    
    if request.POST:
        raise Http404('Content Submission form needs to Post into Alfresco')
    
    form_action = ALFRESCO_CONTENT_SUB_URL
    form = ContentSubmissionForm(initial={'folderId': space_id})
    return render_to_response('alfresco/content_submission_form.html',
            {'form' :form , 'form_action' : form_action}, 
             context_instance=RequestContext(request))


def cache(request):
    """
    A handy little way to clear cache Elements
    """
    if request.POST:
        form = CacheForm(request.POST)
        if form.is_valid():
            for key, value in form.cleaned_data.items():
                if value:
                    image_cache.delete(key)
                    return HttpResponseRedirect(reverse('alfresco_cache'))
    else:
        form = CacheForm(cache=image_cache)
    return render_to_response('alfresco/admin/cache_form.html', {'form':form}, context_instance=RequestContext(request))

@ticket_required 
def ajax_search(request):
    """
    Used for the search box within the admin.
    """
    json = '[]'
    q = request.GET.get('q', None)
    if q:
        ws = service.WebScript('django/','search', format='json')
        ticket = request.user.ticket
        json = ws.search(q='@cm\:title:"%s" TEXT:%s' % (q, q), alf_ticket=ticket, raw=True)        
    return render_to_response('alfresco/ajax_search.json', {'json':json})
        
    
    