from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^login/$',    'alfresco.views.login', name='alfresco_login'),
    url(r'^logout/$',   'alfresco.views.logout', name='alfresco_logout'),
    url(r'^error/$',   'django.views.generic.simple.direct_to_template', {
        'template' : 'alfresco/error.html' }, name='alfresco_error'),
    url(r'^ajax_search/$',   'alfresco.views.ajax_search', name='alfresco_ajax_search'),
)