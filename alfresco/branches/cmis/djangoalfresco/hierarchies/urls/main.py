from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'index/(?P<path>.*)/', 'hierarchies.views.category_index', {}, "category-index"),
)