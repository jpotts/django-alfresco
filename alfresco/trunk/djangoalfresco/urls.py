#
# Copyright 2009 Optaros, Inc.
#
from django.conf.urls.defaults import *
from hierarchies.feeds import CategoryFeed
from hierarchies.models import Category, Hierarchy
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

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
    
    #Sample Site
    (r'^sample_site/', include('sample_site.urls')),
    url(r'^$', 'sample_site.views.home', name='home')
)