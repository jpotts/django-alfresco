from django.conf.urls.defaults import *
from hierarchies.feeds import CategoryFeed
from hierarchies.models import Category, Hierarchy
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line for to enable the admin:
    (r'^admin/hierarchies/', include('hierarchies.urls.admin')),
    url(r'^admin/alfresco/cache/', 'alfresco.views.cache', name='alfresco_cache'),
    url(r'^admin/(.*)', admin.site.root, name='admin_home'),
    (r'^alfresco/', include('alfresco.urls')),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^sample_site/', include('sample_site.urls')),
    url(r'^$', 'sample_site.views.home', name='home')
)