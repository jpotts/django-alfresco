#
# Copyright 2009 Optaros, Inc.
#
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'index/(?P<path>.*)/', 'sample_site.views.category_index', {}, "category-index"),
)