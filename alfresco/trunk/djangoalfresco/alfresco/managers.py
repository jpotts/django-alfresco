#
# Copyright 2009 Optaros, Inc.
#
import datetime

from django.db import models

from alfresco import  service
from alfresco.paginator import AlfrescoSearchPaginator
from log.loggers import logger

def order_by_helper(order_by, object_list):
    if order_by:
        # from http://mail.python.org/pipermail/python-list/2006-May/381137.html
        rev = False
        if order_by.startswith('-'):
            order_by = order_by[1:]
            rev = True
        decorated_list = [(getattr(d,order_by), d) for d in object_list]
        decorated_list.sort()
        if rev:
            decorated_list.reverse()
        object_list = [t[1] for t in decorated_list]
    return object_list

class AlfrescoContentManager(models.Manager):
    
    # Forces the manager to be used for related content.
    use_for_related_fields = True
    
    def get_query_set(self):
        return self.get_empty_query_set()
    
    def get(self, *args, **kwargs):
        #handles the Related Manager case.
        kwargs.update(getattr(self, 'core_filters', {}))
        
        ws = service.WebScript('django/', 'archive')
        try:
            if kwargs.has_key('space__id'):
                web_script_list = ws.get_by_space(*args, **kwargs)
            else:
                web_script_list = ws.get(*args, **kwargs)
        except service.AlfrescoException, e:
            if e.code is 4:
                raise self.model.DoesNotExist, 'No Alfresco content exists with that ID'
            else:
                raise e
        if len(web_script_list) is not 1:
            raise self.model.DoesNotExist('Multiple instances with that Alfresco ID exist')
        else:
            return web_script_list[0]
    
    def filter(self, *args, **kwargs):
        #handles the Related Manager case.
        kwargs.update(getattr(self, 'core_filters', {}))
        if not kwargs.has_key('space__id'):
            #raise NotImplementedError('Filter is not implemented for the Content Manager only the Space Related Manger')
            # Need to return empty for dumpdata to function properly
            logger.error('Filter is not implemented for the Content Manager only the Space Related Manger')
            return []
        
        #Cached model reference. Fast and helps with any potential import errors 
        Space = models.get_model('alfresco', 'space')
        space = Space.objects.get(pk=kwargs.pop('space__id'))
        q = space.q_path_directly_below()
        
        #do the search and sort.
        sws = service.SearchWebScript()
        web_script_list = sws.search(q=q, *args, **kwargs)
        return web_script_list

    def search(self, *args, **kwargs):
        sws = service.SearchWebScript()
        object_list = sws.search(*args, **kwargs)
        return object_list

    """
     I am commenting out all and recursive_all because they are preventing admin delete of a space object from working. The problem is that
     kwargs does not contain alf_ticket like it does for some of these other methods.
    """
    
#    def all(self, *args, **kwargs):
#        #handles the Related Manager case.
#        kwargs.update(getattr(self, 'core_filters', {}))
#        
#        if not kwargs.has_key('space__id'):
#            #raise NotImplementedError('Filter is not implemented for the Content Manager only the Space Related Manger')
#            # Need to return empty for dumpdata to function properly
#            logger.error('Filter is not implemented for the Content Manager only the Space Related Manger')
#            return []
#            
#        ws = service.WebScript('django/', 'space')
#        kwargs['id'] = kwargs.pop('space__id')
#        web_script_list = ws.get(*args, **kwargs)
#        return web_script_list
    
#    def recursive_all(self, *args, **kwargs):
#        #handles the Related Manager case.
#        kwargs.update(getattr(self, 'core_filters', {}))
#        if not kwargs.has_key('space__id'):
#            raise NotImplementedError('Filter is not implemented for the Content Manager only the Space Related Manger')
#        
#        #Cached model reference. Fast and helps with any potential import errors 
#        Space = models.get_model('alfresco', 'space')
#        space = Space.objects.get(pk=kwargs.pop('space__id'))
#        q = space.q_path_any_below_include() + ' AND PATH:"//cm:Published//*"'
#        
#        #do the search and sort.
#        sws = service.SearchWebScript()
#        web_script_list = sws.search(q=q, *args, **kwargs)
#        return web_script_list
    
    
    def paginate(self, *args, **kwargs):
        # Returns an instance of the Search Paginator
        #handles the Related Manager case.
        kwargs.update(getattr(self, 'core_filters', {}))
        if not kwargs.has_key('space__id'):
            raise NotImplementedError('Filter is not implemented for the Content Manager only the Space Related Manger')
        
        #Cached model reference. Fast and helps with any potential import errors 
        Space = models.get_model('alfresco', 'space')
        space = Space.objects.get(pk=kwargs.pop('space__id'))
        q = space.q_path_directly_below()
        
        #do the search and sort.
        return AlfrescoSearchPaginator(q=q, *args, **kwargs)

class UserManager(models.Manager):
    def create_user(self, username, first, last, email, password, ticket):
        "Creates and saves a User with the given username, e-mail and password."
        now = datetime.datetime.now()
        user = self.model(None, username, first, last, email.strip().lower(), 'placeholder', False, True, False, now, now)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.ticket = ticket
        user.save()
        return user

    