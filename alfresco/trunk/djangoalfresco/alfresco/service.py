#
# Copyright 2009 Optaros, Inc.
#
import urllib2
import datetime
import base64
from xml.dom import minidom
from xml import sax

from django.utils import simplejson
from django.core import serializers
from django.core.cache import cache

from alfresco import settings
from alfresco.cache import image_cache
from alfresco.thumbnail import parse_html_for_images
from alfresco import utils

from log.loggers import logger


HEADER = '<?xml version="1.0" encoding="utf-8"?><django-objects version="1.0">'
FOOTER = '</django-objects>'


class AlfrescoException(Exception):
    """
    Alfresco Exception, We raise it when the webscripts can be reached or something else is wrong.
    """
    def __init__(self, message, code=1):
        self.code = code
        self.message = message
        
    def __str__(self):
        return settings.ALFRESCO_EXCEPTION_CODES[self.code]


class RESTRequest(urllib2.Request):
    """
    Overrides urllib's request default behavior
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', 'GET')
        self._auth = kwargs.pop('auth', None)
        assert self._method in ['GET', 'POST', 'PUT', 'DELETE']
        urllib2.Request.__init__(self, *args, **kwargs)
        if self._auth:
            self.add_header('Authorization', 'Basic %s' %  self._auth)

    def get_method(self):
        return self._method

def get_node_by_id(xml, id_or_list):
    """
    From a xml doc, get only the object with the right ids    
    """
    if not isinstance(id_or_list, list):
        id_or_list = [id_or_list]
    #TODO: Catch exceptions in parsing xml
    doc = minidom.parseString(xml)
    obj_list = doc.getElementsByTagName('object')
    obj_xml = ''
    for obj in obj_list:
        if obj.attributes['pk'].value in id_or_list:
            obj_xml += obj.toxml()
    obj_xml = HEADER + obj_xml + FOOTER
    return obj_xml


class WebScript(object):
    """
    Django Representation of a webscripts.
        package: The alfresco package where the script lives i.e. 'django'
    
    """
    def __init__(self, package, method, format='xml'):
        (self.package, self.method, self.format) = (package, method, format)
        self.url = None
        self.response = None
        self.auth = None

    def _authorize(self, **kwargs):
        
        ticket = kwargs.pop('alf_ticket', None)
        if ticket is None:
            ticket = kwargs.pop('ticket', None)
        
        user = kwargs.pop('user', None)
        password = kwargs.pop('password', None)
        
        #honor the passed in information first
        if ticket:
            self.auth = base64.encodestring(ticket).strip()
        
        elif user is not None and password is not None:
            self.auth = base64.encodestring('%s:%s' % (user, password)).strip()
        else:
            self.auth = base64.encodestring('%s:%s' % (settings.ALFRESCO_DEFAULT_USER, 
                                    settings.ALFRESCO_DEFAULT_USER_PASSWORD)).strip()

    def _build_request(self, *args, **kwargs):
        """
        Builds the query
        """ 
        #Pulls out the ticket or user/pass and sticks it in auth.
        self._authorize(**kwargs)
        print kwargs
        #creates url
        self.url = utils.join(settings.ALFRESCO_SERVICE_URL, self.package, self.method)
        
        if self.format:
            kwargs['format'] = self.format
        #Adds the get params
        query = '&'.join(['%s=%s' % (key, value) for key, value in kwargs.items() if key not in ['alf_ticket', 'ticket', 'user', 'password']])
        
        #Don't work, but would be nice if it did.
        #query = urllib.urlencode(kwargs)
        if query:
            self.url += '?%s' % query.replace(' ', '%20')
        
        logger.info('url: %s' % str(self.url))
        return RESTRequest(self.url, method='GET', auth=self.auth)
        
    def element(self, attr):
        xml = minidom.parseString(self.response)
        element = xml.getElementsByTagName(attr)
        return element[0].firstChild.data
    
    def deserializer(self, **kwargs):
        object_list = []
        deserialized_iter = serializers.deserialize(self.format, self.response)
        #This is less scary than it looks. See below
        while (1):            
            try: 
                """
                The object is lazy loaded. It's only going to try to create the object
                once we call deserialized_object.next()
                
                The default method is:
                for deserialized_object in serializers.deserialize("xml", data):
                    if object_should_be_saved(deserialized_object):
                        deserialized_object.save()
                        
                The problem with this is that if one object fails, than it kills the rest of the loop.
                This way we are able to pass over the bad object and continue with the rest. 
                """
                deserialized_object = deserialized_iter.next()
                obj = deserialized_object.object
                if hasattr(obj, 'content'):
                    html, images = parse_html_for_images(obj.content, kwargs.get('alf_ticket', None))
                    setattr(obj, 'content', html)
                    setattr(obj, 'images', images)
                object_list.append(obj)
            # Iterators Raise this once they are complete. 
            except StopIteration:
                break
            
            except (sax.SAXParseException, serializers.base.DeserializationError), e:
                # Continue onto the next object.
                #TODO: We will need to log this error.
                #logger.error('Exception in alfresco.service.deserializer: %s' % str(e))                    
                continue
        
        return object_list

    def execute(self, *args, **kwargs):
        # Builds the request.
        request = self._build_request(*args, **kwargs)
        try:
            request_response = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code == 401:
                logger.error(settings.ALFRESCO_EXCEPTION_CODES[1]+ 'url :' + self.url )
                raise AlfrescoException(str(e))
            elif e.code == 400:
                logger.error(settings.ALFRESCO_EXCEPTION_CODES[3]+ 'url :' + self.url)
                raise AlfrescoException(str(e), code=3)
            else:
                logger.error(settings.ALFRESCO_EXCEPTION_CODES[4]+ 'url :' + self.url)
                raise AlfrescoException(str(e), code=4)
        except urllib2.URLError, e:
            logger.critical(settings.ALFRESCO_EXCEPTION_CODES[2]+ 'url :' + self.url)
            raise AlfrescoException(str(e),code=2)
        self.response = request_response.read()
        
        
    def get(self, *args, **kwargs):
        raw = kwargs.pop('raw', False)
        
        id = kwargs['id']
        xml = cache.get(id)
        
        if xml:
            self.response = xml
        else:
            self.execute(self, *args, **kwargs)
            cache.set(id, self.response, settings.ALFRESCO_CACHE_FILE_TIMEOUT)
        if raw:
            return self.response
        
        return self.deserializer(**kwargs)
    
    def get_by_space(self, *args, **kwargs):
        """
        Look at the space file. See if there is anything there that we can use.
        """
        space_id = kwargs.pop('space__id')
        id = kwargs['id']
        xml = cache.get(space_id)
        if xml:
            self.response = get_node_by_id(xml, id)
        else:
            kwargs['id'] = space_id
            self.method = 'space'
            self.execute(self, *args, **kwargs)
            cache.set(space_id, self.response, settings.ALFRESCO_CACHE_FILE_TIMEOUT)
            self.response = get_node_by_id(self.response, id)
        raw = kwargs.get('raw', False)
        if raw:
            return self.response
        return self.deserializer(**kwargs)

    def search(self, *args, **kwargs):
        #TODO. Will go away once Alfresco 3.0 is in.
        self.execute(self, *args, **kwargs)
        raw = kwargs.get('raw', False)
        if raw:
            return self.response
        return self.deserializer(**kwargs)
    
class SearchWebScript(WebScript):
    """
    Takes the following params:
        q:
        sort_by:
        limit:
        page:
        page_size:
    
    use: 
    >>> s = SearchWebScript()
     <alfresco.service.SearchWebScript object at 0x885076c>
    >>> s.search(q='ALL:image', sort_by='-modified', alf_ticket=ticket, limit=1)
    [<Content: ae284cb4-4786-4dcd-90a6-895fd4a5db65 - RSS_2.0_recent_docs.ftl>]
    
    >>> s.search(q='ALL:image', sort_by='-modified', alf_ticket=ticket, page=1, page_size=2)
    ({u'num_pages': u'2', u'num_results': u'3', u'page': u'1', u'page_size': u'2',
       ...
    [<Content: e32ec162-9447-4878-b1e8-6cf8678bec2c - general_example.ftl>,
    <Content: 98dff7e4-d184-41bd-8ea3-0172b66c81d8 - my_docs_inline.ftl>])
    """
    def __init__(self, package='django', method='sortedsearch', format='xml'):
        (self.package, self.method, self.format) = (package, method, format)
        self.url = None
        self.response = None
        self.params = {}
    
    def paginate(self, *args, **kwargs):
        #We need to require a page and a page_size to paginate
        if not kwargs.has_key('page') and not kwargs.has_key('page_size'):
            raise KeyError('To paginate, we need both a page and a page_size')
        if 'sort_by' not in kwargs:
            kwargs['sort_by'] = kwargs.pop('order_by', '-modified')
        self.execute(self, *args, **kwargs)
        self.parse_search_results()
        return self.params, self.deserializer(**kwargs)
    
    def search(self,*args, **kwargs):
        if 'sort_by' not in kwargs:
            kwargs['sort_by'] = kwargs.pop('order_by', '-modified')
        raw = kwargs.pop('raw', False)
        self.execute(self, *args, **kwargs)
        if raw:
            return self.response
        else:
            return self.deserializer(**kwargs)
        
    def parse_search_results(self):
        doc = minidom.parseString(self.response)
        search_result_element = doc.firstChild
        result_params = search_result_element.getElementsByTagName('params')[0]
        django_objects = search_result_element.getElementsByTagName('django-objects')[0]
        for value in result_params.getElementsByTagName('value'):
            self.params[value.attributes['name'].value] = value.firstChild.data
        self.response = django_objects.toxml()


def generic_search(q, sort_by, limit, alf_ticket, cache_results=False, limit_range=False):
    """
    Wrapper for SearchWebScript
    """
    KEY = None
    if cache_results:
        from alfresco.utils import generate_hex_key
        KEY = generate_hex_key(q,sort_by,limit)
        value = cache.get(KEY)
        if value:
            logger.info("cached generic_search value: %s" % value)
            return value
    sws = SearchWebScript()
    
    if limit_range:
        max = datetime.date.today()
        min = max - datetime.timedelta(days=settings.ALFRESCO_QUERY_LIMIT_RANGE)
        q=q + 'AND @cm\:modified:[%sT00:00:00 TO %sT00:00:00]' % (min,max)
        
    value = sws.search(q=q, sort_by=sort_by, limit=limit, alf_ticket=alf_ticket)
    if cache_results:
        cache.set(KEY, value, settings.ALFRESCO_GENERIC_SEARCH_CACHE_TIMEOUT)
    return value

class SpaceStore(object):
    """
    Used to get things like Images out of the Alfresco's Space Store.
    On the get call it will download the image locally then return the local URL.
    
    Use::
        >>> from alfresco.service import SpaceStore
        >>> ss = SpaceStore(ticket='TICKET_c6d6fbd0a435ec3a8e72aa9ddb68ecd348c00e42', id='e84aab7a-a9e7-11dd-b16e-6fe7aa3ccecc')
        >>> ss.get()
        /site_media/alfresco/images/e84aab7a-a9e7-11dd-b16e-6fe7aa3ccecc.png
    """
    def __init__(self, ticket, path=None, id=None, file_name=None, *args, **kwargs):
        
        self.extension = None
        self.path = path
        self.id = id
        self.url = None
        self.ticket = ticket
        
        if path:
            self.id = path.split('/')[0]
            self.extension = path.split('.')[-1]
        elif id and file_name:
            self.path = id +'/'+ file_name
            self.extension = file_name.split('.')[-1]
        elif not id:
            raise ValueError('SpaceStore either needs the a path or an id')
    
    def _build_url(self):
        if not self.path:
            from alfresco.models import Content
            content = Content.objects.get(id=self.id, alf_ticket=self.ticket)
            self.path = '/'.join([content.id,content.name])
            self.extension = content.name.split('.')[-1]    
            
        self.url = settings.ALFRESCO_SPACE_STORE_URL + self.path + '?ticket=%s' % self.ticket
        logger.info('SpaceStore downloading content from: %s' % self.url)
         
    def get(self):
        """
        Returns the local url reference.
        """
        url = image_cache.get(self.id, self.extension)
        if not url:
            self._build_url()
            request = urllib2.Request(self.url)
            try:
                request_response = urllib2.urlopen(request)
            except urllib2.HTTPError, e:
                if e.code == 401:
                    logger.error(settings.ALFRESCO_EXCEPTION_CODES[1]+ 'url :' + self.url )
                    raise AlfrescoException(str(e))
                elif e.code == 400:
                    logger.error(settings.ALFRESCO_EXCEPTION_CODES[3]+ 'url :' + self.url)
                    raise AlfrescoException(str(e), code=3)
                else:
                    logger.error(settings.ALFRESCO_EXCEPTION_CODES[4]+ 'url :' + self.url)
                    raise AlfrescoException(str(e), code=4)
            except urllib2.URLError, e:
                logger.critical(settings.ALFRESCO_EXCEPTION_CODES[2]+ 'url :' + self.url)
                raise AlfrescoException(str(e),code=2)
            url = image_cache.set(self.id, self.extension, request_response.read())
        return url    
    

######################
### Authentication ###
######################

def login(username, password):
    """
    Used to obtain a ticket for a user from Alfresco.
    
    >>> from alfresco.service import login
    >>> login('admin', 'admin')
    u'TICKET_c6d6fbd0a435ec3a8e72aa9ddb68ecd348c00e42'
    """
    ws = WebScript('api/', 'login', format='xml')
    ws.execute(u=username, pw=password)
    return ws.element('ticket')    

def logout(ticket):
    ws = WebScript('api/', 'login/ticket/')
    ws.url += ticket
    ws.send()
    
def get_person(username, ticket):
    """
    Returns a dictionary of a person's attributes. Alfresco 3.0 only.
    """
    ws = WebScript('api', 'people/%s' % username , None)
    ws.execute(alf_ticket=ticket)
    return simplejson.loads(ws.response)

######################
####  Navigation  ####
######################

def get_navigation_ul(ticket):
    """
    UL Representation of the navigation
    
    Writes a file to file_cache containining data used to
    build the space tree navigation for django space admin
    """
    key = settings.ALFRESCO_SPACE_NAVIGATION_CACHE_KEY
    html = cache.get(key)
    if not html:
        #TODO: Reconsider this, if force=True, it will NEVER update the cache if the file exists...
        if not html:
            logger.debug('Started building navigation tree')
            json = {'root': {'id': settings.ALFRESCO_SPACE_NAVIGATION_ROOT_ID, 'title': 'root',  'children': []}}
            _recurse_node(settings.ALFRESCO_SPACE_NAVIGATION_ROOT_ID, json, ticket)
            html = '<ul id="tree" class="treeview">' + _recurse_ul(json['children']) + '</ul>'
            cache.set(key, html, settings.ALFRESCO_SPACE_NAVIGATION_ROOT_CACHE_TIMEOUT)
            logger.debug('Finished building navigation tree')
        else:
            cache.set(key, html, settings.ALFRESCO_SPACE_NAVIGATION_ROOT_CACHE_TIMEOUT)
    return html
        
def _get_node(ticket, id):
    ws = WebScript('django/', 'nav')
    kwargs = {"alf_ticket" : ticket}
    if id:
        kwargs["id"] = id
    ws.execute(**kwargs)
    return simplejson.loads(ws.response)
    
def _recurse_node(id, parent, ticket):
    children = _get_node(ticket, id)
    parent['children'] = children
    for child in parent['children']:
        _recurse_node(child['id'], child, ticket)
    
def _recurse_ul(node_list):
    str = ""
    for child in node_list:
        str += '<li><a href="?%s">%s</a> <a href="#" onclick="fillForm(\'%s\',\'%s\',\'%s\',\'%s\')"> Select </a>' \
                % ( child['id'], child['name'], child['id'], child['name'], child['path'],child['qname'],)
        if child['children']:
            str += '<ul>%s</ul>' % _recurse_ul(child['children'])
        str += '</li>'
    return str