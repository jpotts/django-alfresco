"""
The plan is for this to replace service.py

It should not be dependant on anything Django. 

TODO: Create a python object around a workspace.
    Pass back that object and with it we can get at the rest of the repository
    
    use:
        from alfresco import cmis
        #login user
        workspace = cmis.Workspace('http://localhost:8080/alfresco/service/api')
        #authentication
        ticket = workspace.login('admin', 'admin')
        #children
        workspace.get_root_children(ticket)
        #query
        workspace.query('select * from BLOG', ticket)
        #post
        workspace.add_folder(parent_id, {'title':'new_folder'}, ticket)
        #Stream Content
        workspace.get(id, ticket)

"""
import urllib2
#Doesn't work. 
import feedparser
import base64
from xml.dom import minidom
from xml.etree import ElementTree
import re

NS_RE = re.compile('{.*?}')

ATOM_NAMESPACE = u'http://www.w3.org/2005/Atom'
CMIS_NAMESPACE = u'http://www.cmis.org/2008/05'

class RESTRequest(urllib2.Request):
    """
    Overrides urllib's request default behavior
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', 'GET')
        self._ticket = kwargs.pop('ticket', None)
        assert self._method in ['GET', 'POST', 'PUT', 'DELETE']
        urllib2.Request.__init__(self, *args, **kwargs)
        if self._ticket:
            # The strip is very important and took 6 hours of my life to fix.
            self.add_header('Authorization', 'Basic %s' % base64.encodestring(self._ticket).strip())

    def get_method(self):
        return self._method

#Taken from posixpath.py
def join(a):
    """Join two or more pathname components, inserting '/' as needed"""
    path = a.pop(0)
    for b in a:
        if b is None:
            continue
        if b.startswith('/'):
            path = b
        elif path == '' or path.endswith('/'):
            path +=  b
        else:
            path += '/' + b
    return path

def clean_tag(tag):
    return NS_RE.sub('', tag)
    
#Taken from http://code.activestate.com/recipes/573463/
class XmlDictObject(dict):
    #TODO
    def __init__(self, initdict=None):
        if initdict is None:
            initdict = {}
        dict.__init__(self, initdict)
    
    def __getattr__(self, item):
        return self.__getitem__(item)
    
    def __setattr__(self, item, value):
        self.__setitem__(item, value)
    
    def __str__(self):
        if self.has_key('_text'):
            return self.__getitem__('_text')
        else:
            return ''

def _ConvertXmlToDictRecurse(node, dictclass):
    nodedict = dictclass()
    
    if len(node.items()) > 0:
        # if we have attributes, set them
        for a, v in node.items():
            nodedict[clean_tag(a)] = v
    
    for child in node:
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, dictclass)
        if nodedict.has_key(clean_tag(child.tag)):
            # found duplicate tag, force a list
            if type(nodedict[clean_tag(child.tag)]) is type([]):
                # append to existing list
                nodedict[clean_tag(child.tag)].append(newitem)
            else:
                # convert to list
                nodedict[clean_tag(child.tag)] = [nodedict[clean_tag(child.tag)], newitem]
        else:
            # only one, directly set the dictionary
            nodedict[clean_tag(child.tag)] = newitem

    if node.text is None: 
        text = ''
    else: 
        text = node.text.strip()
    
    if len(nodedict) > 0:            
        # if we have a dictionary add the text as a dictionary value (if there is any)
        if len(text) > 0:
            nodedict['_text'] = text
    else:
        # if we don't have child nodes or attributes, just set the text
        if node.text:
            nodedict = node.text.strip()
        else:
            nodedict = ""
    return nodedict
        
def ConvertXmlToDict(root, dictclass=XmlDictObject):
    return dictclass({clean_tag(root.tag): _ConvertXmlToDictRecurse(root, dictclass)})

def parse_response(response):
    response_type = response.headers.subtype
    
    if response_type == 'atom+xml':
        return ConvertXmlToDict(ElementTree.fromstring(response.read()))
    else:
        return response.read()

class CMISFeedParser(object):
    """
    Couple of different feeds here. Service and Feed, we care mostly about feed.     
    """
    def __init__(self):
        self.doc = {}
        
    def parse(self, xml):
        doc = minidom.parseString(xml)
        first_element = doc.firstChild
        if first_element.tagName == 'feed':
            self.parse_feed(first_element)
        elif first_element.tagName == 'service':
            self.parse_service(first_element)


    def _parse_service(self, elem):
        """
        workspaces --> workspace title - 
        
        """
        workspaces = {}
        for ws in elem.getElementsByTagName('workspace'):
            ws_children = [j for j in ws.childNodes if j.nodeType is not minidom.Node.TEXT_NODE]
            
    def _node_to_dict(self, node):
        pass
    
class CMISDocument(minidom.Document):
    """
    Stuctures the XML for Put and Post commmands.
    """
    namespace = 'cmis'
    
    def __init__(self):
        minidom.Document.__init__(self)
        self.entry = self.createElement('entry')
        self.entry.setAttribute("xmlns", "http://www.w3.org/2005/Atom")
        self.entry.setAttributeNS('xmlns', 'xmlns:cmis', "http://www.cmis.org/2008/05")
        self.appendChild(self.entry)    
    
    def toxml(self, encoding = "utf-8"):
        return minidom.Document.toxml(self, encoding)

    def toprettyxml(self, indent="\t", newl="\n", encoding = 'utf-8'):
        return minidom.Document.toprettyxml(self, indent, newl, encoding)

    def setProperties(self, prop_dict={}):
        for key, value in prop_dict.items():
            elem = self.createElement(key)
            text_node = self.createTextNode(value)
            elem.appendChild(text_node)
            self.entry.appendChild(elem)
    
    def setCMISProperties(self, prop_dict={}):
        #UGLY
        cmis_object = self.createElementNS(self.namespace, 'cmis:object')
        cmis_properties = self.createElementNS(self.namespace, 'cmis:properties')
        cmis_object.appendChild(cmis_properties)
        for key, value in prop_dict.items():
            elem = self.createElementNS(self.namespace, 'cmis:propertyString')
            elem.setAttributeNS(self.namespace, 'cmis:name', key)
            value_elem = self.createElementNS(self.namespace, 'cmis:value')
            text_node = self.createTextNode(value)
            value_elem.appendChild(text_node)
            elem.appendChild(value_elem)
            cmis_properties.appendChild(elem)
        self.entry.appendChild(cmis_object)
        
class CMISWebScript(object):
    """
    Does makes the acutally request to CMIS
    
        c = CMISWebScript()
        c.put('d47304b8-29f5-4379-9b52-0ae26cc665ca', 'TICKET_45fff4a178006140bc9f5c30a78b91ec092ad279', {'title': 'new folder 4'},)
        
        c.simple('TICKET_45fff4a178006140bc9f5c30a78b91ec092ad279', 'repository')
        Returns a dictionary. 
        
    TODO:
        Error handling.
    """
    def __init__(self, service_url='http://localhost:8080/', service_root='alfresco/service/api'):
        self.service_url = service_url
        self.service_root = service_root
        self.url = None
    
    def _build_url(self, *args, **kwargs):
        self.url = join([self.service_url, self.service_root] + list(args))
        query = '&'.join(['%s=%s' % (key, value) for key, value in kwargs.items()])
        if query:
            self.url = self.url +'?'+query.replace(' ', '%20')
        print self.url
    
    def get(self, id , ticket, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        request = RESTRequest(self.url, method='GET', ticket=ticket)
        request_response = urllib2.urlopen(request)
        return parse_response(request_response)

    def simple(self, ticket, method):
        self._build_url(method)
        request = RESTRequest(self.url, method='GET', ticket=ticket)
        request_response = urllib2.urlopen(request)
        return parse_response(request_response)
    
    def delete(self, id, ticket, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        request = RESTRequest(self.url, method='DELETE', ticket=ticket)
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code is not 204:
                raise e
        return None
    
    def put(self, id, ticket, params, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        doc = CMISDocument()
        doc.setProperties(params)
        request = RESTRequest(self.url, doc.toxml(), method='PUT', ticket=ticket)
        request.add_header('Content-Type', 'application/atom+xml;type=entry')
        request_response = urllib2.urlopen(request)
        return parse_response(request_response)
    
    def post(self, id, ticket, params, cmis_params=None, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        doc = CMISDocument()
        doc.setProperties(params)
        doc.setCMISProperties(cmis_params)
        request = RESTRequest(self.url, doc.toxml(), method='POST', ticket=ticket)
        request.add_header('Content-Type', 'application/atom+xml;type=entry')
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code is not 201:
                raise e
            else:
                return parse_response(e.read())
