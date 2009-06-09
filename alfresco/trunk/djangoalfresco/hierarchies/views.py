#
# Copyright 2009 Optaros, Inc.
#
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404

from hierarchies.models import Category, Hierarchy
from hierarchies import forms

from alfresco.models import Content
from alfresco.decorators import ticket_required
from alfresco.service import generic_search
from alfresco import utils


@ticket_required
def category_detail(request, path, **kwargs):
    cat = get_object_or_404(Category, slug_path=path)
    ticket = request.user.ticket
    recent_docs = []
    if cat.space:
        recent_docs = cat.space.contents.filter(limit=20, order_by='-modified', alf_ticket=ticket)
    return render_to_response(cat.get_templates(), {'recent_docs': recent_docs,
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
    return render_to_response('categories/content_detail.html', 
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
    
    return render_to_response('categories/index.html', 
                              {'page' : paginator.page,
                               'pages' : paginator.pages(),
                               'category': category,
                               'order_by': order_by,
                               'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by)}, 
                                context_instance=RequestContext(request))

@ticket_required
def hierarchy_detail(request, slug, **kwargs):
    hierarchy = get_object_or_404(Hierarchy, slug=slug)
    recent_docs = []
    space = hierarchy.space
    if space:
        recent_docs = generic_search(space.q_path_any_below_include(), '-modified', 20, request.user.ticket, True)
    print hierarchy.get_templates()
    return render_to_response(hierarchy.get_templates(), 
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
def top(request, path):
    cat = get_object_or_404(Category, slug_path=path)
    user = request.user
    
    if not user.has_perm('hierarchies.top_story_editor'):
        return HttpResponseRedirect('%s?next=%s' %(reverse('alfresco_login'), urlquote(request.get_full_path())))
    elif not cat.space:
        return Http404()

    ticket = user.ticket
    if request.POST:
        form = forms.OrderingForm(request.POST)
        if form.is_valid:
            xml = cat.space.contents.recursive_all(alf_ticket=ticket, raw=True, limit=30, sort_by='-modified')
            form.save(cat,xml)
    else:
        form = forms.OrderingForm({'sequence': 'test'})
    
    all_list = cat.space.contents.recursive_all(alf_ticket=ticket, limit=30, sort_by='-modified')
    top_list = cat.get_top_content()
    return render_to_response('categories/admin/top.html', {'all_list': all_list, 'top_list' : top_list,
                                        'category': cat, 'form' : form },context_instance=RequestContext(request) )

#########################
######    ADMIN    ######
#########################
def category_order(request, id):
    category = get_object_or_404(Category, pk=id)
    if request.POST:
        serialize = request.POST['array']
        id_list =  [f.split('=')[1] for f in serialize.split('&')]
        i = 0
        for id in id_list:
            child = Category.objects.get(pk=id)
            child.order = i
            child.save()
            i +=1
        return HttpResponseRedirect('../')
    return render_to_response('categories/admin/order.html', {'categories': category.child.all() },context_instance=RequestContext(request) )

def hierarchy_subcategory_order(request, id):
    hierarchy = get_object_or_404(Hierarchy, pk=id)
    if request.POST:
        serialize = request.POST['array']
        id_list =  [f.split('=')[1] for f in serialize.split('&')]
        i = 0
        for id in id_list:
            child = Category.objects.get(pk=id)
            child.order = i
            child.save()
            i +=1
        return HttpResponseRedirect('../')
    
    return render_to_response('categories/admin/order.html', {'categories': hierarchy.categories.filter(parent=None)},context_instance=RequestContext(request) )

def hierarchy_order(request):
    hierarchies = Hierarchy.objects.all()
    if request.POST:
        serialize = request.POST['array']
        id_list =  [f.split('=')[1] for f in serialize.split('&')]
        i = 0
        for id in id_list:
            child = Hierarchy.objects.get(pk=id)
            child.order = i
            child.save()
            i +=1
        return HttpResponseRedirect('../')
    
    return render_to_response('categories/admin/order.html', {'categories': hierarchies},context_instance=RequestContext(request) )

