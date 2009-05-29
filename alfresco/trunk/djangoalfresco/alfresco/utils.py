from xml.dom import minidom
from alfresco.settings import ALFRESCO_DEFAULT_USER, ALFRESCO_DEFAULT_USER_PASSWORD, ALFRESCO_EXTERNAL_USER_CACHE_TIME_OUT
from django.core.cache import cache

from alfresco.service import login, AlfrescoException

def get_constraints(xml, namespace, constraint, name):
    namespace = namespace.replace(':', '\:')
    values = []
    for element in xml.getElementsByTagName('constraints')[0].getElementsByTagName('constraint'):
        if element.getAttribute('name') == constraint:
            value_list = element.getElementsByTagName('parameter')[0].getElementsByTagName('value')
            for value in value_list:
                text = value.childNodes[0].data
                values.append(('@\{%s\}%s:"%s"' % (namespace,name,text),text),)
            break
    
    return values

def get_external_user_ticket():
    """
    For external sites that use django to serve content we don't want to have them get
    a ticket everytime. let's keep one around for awhile.
    """
    KEY = 'alfresco.utils.get_external_user_ticket.ticket'
    ticket = cache.get(KEY)
    if not ticket:
        try:
            ticket = login(ALFRESCO_DEFAULT_USER, ALFRESCO_DEFAULT_USER_PASSWORD)
        except AlfrescoException:
            #No need to log, login does that.
            return None
        cache.set(KEY, ticket, ALFRESCO_EXTERNAL_USER_CACHE_TIME_OUT)
    return ticket

def generate_hex_key(*args):
    string_key = ':'.join([str(a) for a in args])
    try:
        #hashlib is 2.5, md5 is for 2.4
        import hashlib
    except ImportError:
            import md5
            return md5.new(string_key).hexdigest()
    else:
        return hashlib.md5(string_key).hexdigest()