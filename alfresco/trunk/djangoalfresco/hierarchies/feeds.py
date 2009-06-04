#
# Copyright 2009 Optaros, Inc.
#
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from hierarchies.models import Category
from alfresco import service

class CategoryFeed(Feed):
    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        return Category.objects.get(slug_path='/'.join(bits))

    def title(self, obj):
        return "Top Stories for %s" % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return "Top stories from %s" % obj.name

    def items(self, obj):
        
        user = self.request.user
        try:
            recent_docs = service.generic_search(obj.space.q_path_any_below_include(), 
                                                 '-modified', 5, user.ticket, True)            
        except(service.AlfrescoException, AttributeError):
            pass
        #return obj.get_top_content()
        return recent_docs
    
    def item_author_name(self, item):
        return item.author