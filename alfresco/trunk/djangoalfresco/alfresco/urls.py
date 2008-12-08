from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^login/$',    'alfresco.views.login', name='alfresco_login'),
    url(r'^logout/$',   'alfresco.views.logout', name='alfresco_logout'),
    url(r'^content/(?P<id>[-\w]+)/$',   'alfresco.views.content', name='alfresco_content_detail'),
    url(r'^content/print_view/(?P<id>[-\w]+)/$',   'alfresco.views.print_view', name='alfresco_print_view'),
    url(r'^static/(?P<id>[-\w]+)/$', 'alfresco.views.static_content', name='alfresco_static_detail'),
    url(r'^images/(?P<path>.*)',   'alfresco.views.photo', name='alfresco_image'),
    url(r'^search/$',   'alfresco.views.search', name='alfresco_search'),
    url(r'^error/$',   'django.views.generic.simple.direct_to_template', {
        'template' : 'alfresco/error.html' }, name='alfresco_error'),
    url(r'^ajax_search/$',   'alfresco.views.ajax_search', name='alfresco_ajax_search'),
)