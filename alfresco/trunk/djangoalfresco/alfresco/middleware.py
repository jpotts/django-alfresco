#
# Copyright 2009 Optaros, Inc.
#
from alfresco.service import AlfrescoException
from alfresco.settings import  ALFRESCO_DEFAULT_USER, ALFRESCO_DEFAULT_USER_PASSWORD, ALFRESCO_AUTO_LOGIN_ATTEMPTS
from django.contrib.auth import authenticate, login as auth_login
from django.core.urlresolvers import reverse
from django import http

class AlfrescoMiddleware(object):
    """
    Catches Alfresco exceptions. 
    
    -- Ticket exceptions should go back into the login.
    """
    def process_exception(self, request, exception):
        if isinstance(exception, AlfrescoException):
            if exception.code is 1:
                if request.user.username == ALFRESCO_DEFAULT_USER or not request.user.username:
                    #If we have tried to re log in the user 3 times and the page still fails, then give up
                    if request.session.get('alfresco_login_attempts', 0) >= ALFRESCO_AUTO_LOGIN_ATTEMPTS:
                        #reset.
                        request.session['alfresco_login_attempts'] = 0
                        return http.HttpResponseRedirect(reverse('alfresco_error'))
                    else:
                        user = authenticate(username=ALFRESCO_DEFAULT_USER, password=ALFRESCO_DEFAULT_USER_PASSWORD)
                        if user is not None:
                            auth_login(request, user)
                            #increment auto login retries.
                            request.session['alfresco_login_attempts'] = request.session.get('alfresco_login_attempts', 0) + 1
                            #Resubmit the request.
                            return http.HttpResponseRedirect(request.get_full_path())
                else:
                    login_url = reverse('alfresco_login') + '?error=1&next=%s' % request.path
                    return http.HttpResponseRedirect(login_url)
            # Alfresco is not running.
            elif exception.code is 2:
                return http.HttpResponseRedirect(reverse('alfresco_error'))
        
        return None