#
# Copyright 2009 Optaros, Inc.
#
import re
#Django
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.urlresolvers import reverse
#Alfresco
from alfresco.models import Content, StaticContent
from alfresco.decorators import ticket_required
from alfresco import service
from alfresco.forms import LoginForm, ContentSubmissionForm, SearchForm, CacheForm
from alfresco.settings import ALFRESCO_CONTENT_SUB_URL, ALFRESCO_EXCEPTION_CODES
from alfresco.cache import image_cache
from alfresco.paginator import AlfrescoSearchPaginator
from alfresco import utils

#LOGIN 
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


########### CONTENT ############

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

def photo(request, path):
    """
    This is the pass through for images inserted into html via the Alfresco GUI
    """
    ticket = request.user.ticket
    
#    if (slug):
#        sc = StaticContent.objects.get(slug=slug)
#        path = sc.doc_id
    
    if path.find('id/') is 0:
        path = path.split('id/')[1]
    else:
        slug = path
        sc = StaticContent.objects.get(slug=slug)
        path = sc.doc_id
              
    if path.find('.') is -1:
        ss = service.SpaceStore(ticket, id=path)
    else:
        ss = service.SpaceStore(ticket, path=path)
            
    url = ss.get()
    return HttpResponseRedirect(url)


########### SEARCH #############

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
    search_term = utils.create_search_string(request.GET)
    
    #Search
    paginator = AlfrescoSearchPaginator(q=search_term, order_by=order_by, page=page, page_size=page_size, alf_ticket=request.user.ticket)

    #Search Form
    form = SearchForm(initial=utils.clean_q(request.GET))
    
    return render_to_response('alfresco/search.html',
            {'page' : paginator.page,
             'pages': paginator.pages(),
             'search_term': search_term,
             'order_by' : order_by,
             'form' : form,
             'get_params' : utils.make_get_urls(page=page, page_size=page_size, order_by=order_by, q=search_term)}, 
             context_instance=RequestContext(request))

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
    search_term = utils.create_tag_search_string(request.GET)
        
    #Search
    paginator = AlfrescoSearchPaginator(q=search_term, order_by=order_by, page=page, page_size=page_size, alf_ticket=request.user.ticket)

    #Search Form
    form = SearchForm(initial=utils.clean_q(request.GET))
    
    return render_to_response('alfresco/tag_search.html',
            {'page' : paginator.page,
             'pages': paginator.pages(),
             'search_term': search_term,
             'query': query,
             'order_by' : order_by,
             'form' : form,
             'get_params' : utils.make_get_urls(page=page, page_size=page_size, order_by=order_by, q=search_term)}, 
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


        
    
    