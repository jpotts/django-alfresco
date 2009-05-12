from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from alfresco.managers import UserManager
from alfresco import settings

class Repository(models.Model):
    """
    DB Representation of a repository.
    
    Most of the magic here happens in the Manager. 
    We set the auth from a config file.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    url = models.CharField(max_length=200)
    
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    
    def __unicode__(self):
        return u'[%s]%s' % (self.name, self.url)

class Node(models.Model):
    """
    A generic representation of a node in a CMIS repository
    """
    id = models.CharField(primary_key=True, max_length=50, editable=True)
    path = models.CharField(max_length=300, null=True, blank=True)
    repository = models.ForeignKey(Repository, related_name='nodes')
    
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)
    
    #Filters
    types = models.CharField(max_length=200)
    filters = models.CharField(max_length=200)
    order_by = models.CharField(max_length=200)
    
    def __unicode__(self):
        return u'%s' % self.id

class View(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    url = models.CharField(max_length=200)

    def __unicode__(self):
        return u'[%s]%s' % (self.name, self.url)

class AlfrescoUser(User):
    """
    Alfresco User. 
        Extends the User model to apply the ticket.
    """
    ticket = models.CharField(max_length=50, blank=True, null=True)
    objects = UserManager()
    
    def default_user_login(self):
        """
        Used in template tags to log in a user.
        """
        if self.username != settings.ALFRESCO_DEFAULT_USER:
            # TODO: If user is not default direct them to login page
            #   get ticket and return it.
            return None
        from alfresco.service import login
        ticket = login(settings.ALFRESCO_DEFAULT_USER, settings.ALFRESCO_DEFAULT_USER_PASSWORD)
        self.ticket = ticket
        self.save()
        return ticket