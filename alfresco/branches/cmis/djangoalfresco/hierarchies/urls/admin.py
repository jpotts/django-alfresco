from django.conf.urls.defaults import *

urlpatterns = patterns('',
       (r'^category/(?P<id>\d+)/order/$', 'hierarchies.views.category_order'),
       (r'^hierarchy/(?P<id>\d+)/order/$', 'hierarchies.views.hierarchy_subcategory_order'),
       (r'^hierarchy/order/$', 'hierarchies.views.hierarchy_order'),
)