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

def make_get_urls(**kwargs):
    """
    Useful Helper to keep track of the get params.
    Use:
        'get_params' : make_get_urls(page=page, page_size=page_size, order_by=order_by)
    Template
        href="{{get_params.page}}page=1"
    html:
        href="?page_size=10&order_by=modified&page=1"
    """
    r = {}
    keys = kwargs.keys()
    for k in keys:
        n = {}
        for key, value in kwargs.items():
            if key != k and value:
                n[key] = value
        r[k] = '?' + '&'.join(['%s=%s' % (i, v) for i, v in n.items()])
        if len(r[k]) is not 1:
            r[k] += '&'
    return r

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

