from django.conf.urls.defaults import *
from hierarchies.feeds import CategoryFeed
from hierarchies.models import Category, Hierarchy
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

feeds = {
    'categories': CategoryFeed,
}

urlpatterns = patterns('',
    # Uncomment the next line to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line for to enable the admin:
    (r'^admin/hierarchies/', include('hierarchies.urls.admin')),
    url(r'^admin/alfresco/cache/', 'alfresco.views.cache', name='alfresco_cache'),
    url(r'^admin/(.*)', admin.site.root, name='admin_home'),
    (r'^alfresco/', include('alfresco.urls')),
    url(r'^site_map/$', 'django.views.generic.simple.direct_to_template', {
        'template' : 'site_map.html' }, name='site_map'),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^$', 'hierarchies.views.home', name='home'),
    url(r'top/(?P<path>.*)/', 'hierarchies.views.top', {}, "category_top_stories"),
    url(r'index/(?P<path>.*)/', 'hierarchies.views.category_index', {}, "category-index"),
    url(r'external/(?P<path>.*)/', 'hierarchies.views.external_category_recent_documents', {}, "external_category_recent_documents"),
    url(r'^rss/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
        {'feed_dict': feeds}, name='rss_feed'),
    url(r'^(?P<slug>[-\w]+)/$','hierarchies.views.hierarchy_detail', 
        {'queryset' : Hierarchy.objects.all(), 'slug_field' : 'slug'}, name='hierarchy_detail'),
    url(r'^(?P<path>.*)/content/(?P<id>[-\w]+)/$$', 'hierarchies.views.category_content_detail', name='category_content_detail'),
    url(r'^(?P<path>.*)/$', 'hierarchies.views.category_detail', 
        {'queryset' : Category.objects.all(), 'slug_field' : 'slug'}, name='category_detail'),
)