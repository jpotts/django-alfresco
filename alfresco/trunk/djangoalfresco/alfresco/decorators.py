from django.http import HttpResponseRedirect
from django.utils.http import urlquote
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.
    
from alfresco.settings import  ALFRESCO_DEFAULT_USER, ALFRESCO_DEFAULT_USER_PASSWORD
from log.loggers import logger

def ticket_required(viewfunc):
    """
    Decorator that assures the user has a ticket. This however doesn't assure 
    that the user has a valid ticket. Might need to ping alfresco here, but it 
    would cause some issues
    
    Two types of users. 
        AnonymousUser: Doesn't have a ticket. We need them too
        Authenticated user: Has a ticket.
    """
    def _ticket_require(request, *args, **kw):
        user = request.user
        # AnonymousUser or AuthUser doesn't have a ticket
        if not hasattr(user, 'ticket') or user.ticket is None:
                login_url  = '%s?next=%s' %(reverse('alfresco_login'), urlquote(request.get_full_path()))     
                # If it's the Default User or the Anonymous user.
                if settings.AUTO_LOGIN and (user.username == ALFRESCO_DEFAULT_USER or not user.username):
                    user = authenticate(username=ALFRESCO_DEFAULT_USER, password=ALFRESCO_DEFAULT_USER_PASSWORD)
                    if user is not None:
                        auth_login(request, user)
                        logger.info('Auto-login with %s' % ALFRESCO_DEFAULT_USER)
                    else:
                        #TODO Handle the case where the auth_login fails, currently just tossing up the login page
                        logger.error('Auto-login failed with %s' % ALFRESCO_DEFAULT_USER)
                        return HttpResponseRedirect(login_url)
                else:
                    return HttpResponseRedirect(login_url)
        response = viewfunc(request, *args, **kw)
        return response
    return wraps(viewfunc)(_ticket_require)