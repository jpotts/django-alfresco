from django.conf.urls.defaults import *
from hierarchies.feeds import CategoryFeed
from hierarchies.models import Category, Hierarchy

feeds = {
    'categories': CategoryFeed,
}

urlpatterns = patterns('',
    url(r'^site_map/$', 'django.views.generic.simple.direct_to_template', {
        'template' : 'site_map.html' }, name='site_map'),
    url(r'^$', 'sample_site.views.home', name='home'),
    url(r'^static/(?P<id>[-\w]+)/$', 'sample_site.views.static_content', name='static_detail'),
    url(r'^content/(?P<id>[-\w]+)/$',   'sample_site.views.content', name='content_detail'),
    url(r'^content/print_view/(?P<id>[-\w]+)/$',   'sample_site.views.print_view', name='print_view'),
    url(r'^(?P<slug>[-\w]+)/$','sample_site.views.hierarchy_detail', 
        {'queryset' : Hierarchy.objects.all(), 'slug_field' : 'slug'}, name='hierarchy_detail'),
    url(r'^(?P<path>.*)/content/(?P<id>[-\w]+)/$$', 'sample_site.views.category_content_detail', name='category_content_detail'),
    url(r'^(?P<path>.*)/$', 'sample_site.views.category_detail', 
        {'queryset' : Category.objects.all(), 'slug_field' : 'slug'}, name='category_detail'),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    url(r'^image/(?P<path>.*)',   'sample_site.views.photo', name='image'),
    url(r'^search/$',   'sample_site.views.search', name='search'),
    url(r'^tag_search/$',   'sample_site.views.tag_search', name='tag_search'),
)