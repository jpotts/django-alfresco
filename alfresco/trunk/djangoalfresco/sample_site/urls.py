from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^content/(?P<id>[-\w]+)/$',   'sample_site.views.content', name='content_detail'),
    url(r'^content/print_view/(?P<id>[-\w]+)/$',   'sample_site.views.print_view', name='print_view'),
    url(r'^static/(?P<id>[-\w]+)/$', 'sample_site.views.static_content', name='static_detail'),
    url(r'^images/(?P<path>.*)',   'sample_site.views.photo', name='image'),
    url(r'^search/$',   'sample_site.views.search', name='search'),
)