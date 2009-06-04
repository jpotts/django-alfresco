#
# Copyright 2009 Optaros, Inc.
#
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from alfresco.managers import AlfrescoContentManager, UserManager
from alfresco.fields import AlfrescoField
from alfresco import settings

class Space(models.Model):
    """
    Space is a reference to a Alfresco Space.
        id: Alfresco's GUID for a Space, also used as the Primary Key
        name: cm:name property
        path: User friendly path to a Space
        qname: Properly escaped reference to an Alfresco Space. Important for Search
    
    use:
        >> space = Space.objects.all()[0]
         <Space: 3894d193-69bf-11dd-b9c1-e54ed0219b63 - the-Paper>
        
        >> space.contents.all(alf_ticket='TICKET_69561050790e2c5a51a66ad1ee6012c83f3b478e')
         [<Content: 241a8648-69c3-11dd-b9c1-e54ed0219b63 - The Paper>,
         <Content: 1f5baa1e-737d-11dd-99dd-a301046bdff1 - django_assembly.txt>]
        
        >> space.contents.get(id='241a8648-69c3-11dd-b9c1-e54ed0219b63', alf_ticket='TICKET_69561050790e2c5a51a66ad1ee6012c83f3b478e')
         <Content: 241a8648-69c3-11dd-b9c1-e54ed0219b63 - The Paper>
    """
    id = models.CharField(primary_key=True, max_length=50, editable=True)
    name = models.CharField(max_length=150)
    path = models.CharField(max_length=300, null=True, blank=True)
    qname = models.CharField(max_length=500)
            
    def __unicode__(self):
        return u'%s - %s' % (self.id, self.name)
    
    # See http://wiki.alfresco.com/wiki/Search#Path_Queries
    def q_path_directly_below(self):
        # PATH:"/sys:user/*"
        return 'PATH:"%s/*"' % self.qname
    
    def q_path_any_below(self):
        #To find all nodes at any depth below "/sys:user"
        return 'PATH:"%s//*"' % self.qname
    
    def q_path_any_below_include(self):
        #To find all nodes at any depth below "/sys:user" including the node "/sys:user"
        return 'PATH:"%s//."' % self.qname

class Content(models.Model):
    """
    Acts as a pass through for Alfresco Content.
    
    use:
        >> content = Content.objects.get(id='241a8648-69c3-11dd-b9c1-e54ed0219b63', alf_ticket='TICKET_69561050790e2c5a51a66ad1ee6012c83f3b478e')
         <Content: 241a8648-69c3-11dd-b9c1-e54ed0219b63 - The Paper>
        >> content.space
         <Space: 3894d193-69bf-11dd-b9c1-e54ed0219b63 - the-Paper>
    """
    id = models.CharField(primary_key=True, max_length=50)
    space = models.ForeignKey(Space, related_name="contents")
    name = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=100)
    size= models.CharField(max_length=50)
    description= models.CharField(max_length=500, blank=True, null=True)
    title  = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    created = models.DateField()
    modified = models.DateField()
    url = models.CharField(max_length=255, blank=True, null=True)
    tags = models.CharField(max_length=1024, blank=True, null=True)
  
    objects = AlfrescoContentManager()
    
    def __unicode__(self):
        return u'%s - %s' % (self.id, self.name)
    
    def get_absolute_url(self):
        try:
            #Reach goal. If the content exists in both a space and a category then use this URL
            return reverse('category_content_detail',args=[self.space.category.slug_path, self.id])
        except:
            #Safety. Doesn't do breadcrumbs.
            return reverse('content_detail',args=[self.id])

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

class StaticContent(models.Model):
    """
    Acts as a easily referenceable pointer to Alfresco Content
    """
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50)
    description= models.TextField(max_length=500)
    doc_id = AlfrescoField(max_length=50)
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
    def get_absolute_url(self):
        return reverse('content_detail',args=[self.doc_id])