#
# Copyright 2009 Optaros, Inc.
#
from django.conf.urls.defaults import *
from hierarchies.feeds import CategoryFeed
from hierarchies.models import Category, Hierarchy
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

feeds = {
    "categories" : CategoryFeed,
}

urlpatterns = patterns('',
    #ADMIN
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),    
    (r'^admin/hierarchies/', include('hierarchies.urls')),
    url(r'^admin/alfresco/cache/', 'alfresco.views.cache', name='alfresco_cache'),
    url(r'^admin/(.*)', admin.site.root, name='admin_home'),

    #ALFRESCO
    (r'^alfresco/', include('alfresco.urls')),
    
    #MEDIA
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        
    url(r'^site_map/$', 'django.views.generic.simple.direct_to_template', {'template' : 'site_map.html' }, name='site_map'),
    url(r'^$', 'django.views.generic.simple.direct_to_template', {"template": "home.html"}, name='home'),
    
    
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}), 
    
    url(r'^(?P<slug>[-\w]+)/$','hierarchies.views.hierarchy_detail', 
        {'queryset' : Hierarchy.objects.all(), 'slug_field' : 'slug'}, name='hierarchy_detail'),
    url(r'^(?P<path>.*)/content/(?P<id>[-\w]+)/$$', 'hierarchies.views.category_content_detail', name='category_content_detail'),
    url(r'^(?P<path>.*)/$', 'hierarchies.views.category_detail', 
        {'queryset' : Category.objects.all(), 'slug_field' : 'slug'}, name='category_detail'),
    
)