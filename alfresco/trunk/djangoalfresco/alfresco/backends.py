#
# Copyright 2009 Optaros, Inc.
#
from alfresco.models import AlfrescoUser
from alfresco import service
from log.loggers import logger
from django.contrib.auth.backends import ModelBackend

class AlfrescoBackend(ModelBackend):
    """
    Authenticate against the settings ADMIN_LOGIN and ADMIN_PASSWORD.

    Use the login name, and a hash of the password. For example:

    ADMIN_LOGIN = 'admin'
    ADMIN_PASSWORD = 'sha1$4e987$afbcf42e21bd417fb71db8c66b321e9fc33051de'
    """
    def authenticate(self, username=None, password=None):
        user = None
        
        try:
            user = AlfrescoUser.objects.get(username=username)
        except:
            #if no user exists it will create one
            pass
        
        try:
            alf_ticket = service.login(username, password)
        except service.AlfrescoException, a:
            if a.code is not 2:
                return None
            #If alfresco is down we want to tell the user.
            raise a
        
        if user:
            user.ticket = alf_ticket
            user.save()
        else:
            try:
                #Alfresco 3.0 Specific
                person = service.get_person(username, alf_ticket)
                email = person.get('email', '')
                
                if not email:
                    #We need to make sure there is an email for everyuser.
                    email = '%s@optaros.com' % username
                
                first = person.get('firstName', '')
                last = person.get('lastName', '')
                user = AlfrescoUser.objects.create_user(username, first, last,email, password, alf_ticket)
                
                # Used for the Alfresco default admin user
                if username == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
            
            except Exception, e:
                logger.error('Failed to create user for %s. Exception: %s' % (username, str(e)))
        
        return user
    
    def get_user(self, user_id):
        try:
            return AlfrescoUser.objects.get(pk=user_id)
        except AlfrescoUser.DoesNotExist:
            return None