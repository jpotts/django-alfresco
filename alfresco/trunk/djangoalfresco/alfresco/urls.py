#
# Copyright 2009 Optaros, Inc.
#
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^login/$',    'alfresco.views.login', name='alfresco_login'),
    url(r'^logout/$',   'alfresco.views.logout', name='alfresco_logout'),
    url(r'^error/$',   'django.views.generic.simple.direct_to_template', {
        'template' : 'alfresco/error.html' }, name='alfresco_error'),
    url(r'^ajax_search/$',   'alfresco.views.ajax_search', name='alfresco_ajax_search'),
    url(r'^static/(?P<id>[-\w]+)/$', 'alfresco.views.static_content', name='static_detail'),
    url(r'^content/(?P<id>[-\w]+)/$',   'alfresco.views.content', name='content_detail'),
    url(r'^content/print_view/(?P<id>[-\w]+)/$',   'alfresco.views.print_view', name='print_view'),
    url(r'^search/$',   'alfresco.views.search', name='search'),
    url(r'^tag_search/$',   'alfresco.views.tag_search', name='tag_search'),
    url(r'^image/(?P<path>.*)',   'alfresco.views.photo', name='image'), 
)