"""
The plan is for this to replace service.py

It should not be dependant on anything Django. 

Cmis does not have the idea of Login. It should be handled by calling framework. 


    
use:
    from alfresco import cmis
    #Note. the defualt user creditials will be used if no other auth is given
    repository = cmis.Repository('http://localhost:8080/', 'alfresco/service/api', 'admin', 'admin') 
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
import base64
from xml.dom import minidom
from xml.etree import ElementTree
import re
from  datetime import datetime
from time import strptime

NS_RE = re.compile('{.*?}')

ATOM_NAMESPACE = u'http://www.w3.org/2005/Atom'
CMIS_NAMESPACE = u'http://www.cmis.org/2008/05'

#Place holder for now.
ENUMS = {
'enumDecimalPrecision' :[ 32, 64],
'enumContentStreamAllowed ' : ['notallowed', 'allowed', 'required'],
'enumCardinality' : ['single',' multi'],
'enumUpdateability' : ['readonly', 'readwrite', 'whencheckedout'],
'enumPropertyType' : ['Boolean', 'id', 'integer', 'datetime', 'decimal','html', 'uri', 'xml'],
'enumCollectionType' : ['root-children', 'root-descendants', 'unfiled', \
                        'checkedout', 'types-children', 'types-descendants', 'query'],
'enumObjectType' : ['document', 'folder', 'relationship', 'policy'],
'enumCapabilityQuery' : ['none', 'metadataonly', 'fulltextonly', 'both'],
'enumCapabilityJoin' : ['nojoin', 'inneronly', 'innerandouter'],
'enumCapabilityFullText' : ['none', 'fulltextonly', 'fulltextandstructured'],
'enumRepositoryRelationship' : ['self', 'replica', 'peer', 'parent', 'child', 'archive'],
'enumTypesOfFileableObjects' : ['documents', 'folders,' 'policies', 'any'],
'enumVersioningState' : ['checkedout', 'minor', 'major'],
'enumReturnVersion' : ['this', 'latest', 'latestmajor'],
'enumUnfileNonfolderObjects' : ['unfile', 'deletesinglefiled', 'delete'],
'enumRelationshipDirection' : ['source', 'target', 'both'],
'enumIncludeRelationships' : ['none', 'source', 'target', 'both'],
}

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
            self.add_header('Authorization', 'Basic %s' % self._auth)

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

def to_date_time(value):
    return datetime(*strptime(value[:-10], "%Y-%m-%dT%H:%M:%S")[0:6])

########################################################
#Taken from http://code.activestate.com/recipes/573463/#
########################################################
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
    
    def __delattr__(self, item):
        self.__delitem__(item)
        
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
########################################################

class Links(dict):
    def __init__(self, initlist, repository):
        initdict = {'_repository': repository}
        for item in initlist:
            key = item['rel'].replace('-', '_')
            initdict[key] = item['href']
        dict.__init__(self, initdict)
    
    def __getattr__(self, item):
        href = self.__getitem__(item)
        request = RESTRequest(href, method='GET', auth=self['_repository'].service.auth)
        response = urllib2.urlopen(request)
        return CMISFeedParser(response, self['_repository']).parse()
    
    def __setattr__(self, item, value):
        self.__setitem__(item, value)
    
    def __delattr__(self, item):
        self.__delitem__(item)
    
    

class Node(object):
    """
    Representation of Alfresco Node
    """
    def __init__(self, entry, repository, *args, **kwargs):
        self.repository = repository;
        self.author = entry.author
        self.content = entry.content
        self.edited = to_date_time(entry.edited)
        self.icon = entry.icon
        self.id = entry.id
        self.published = to_date_time(entry.published)
        self.summary = entry.summary
        self.terminator = entry.terminator
        self.title = entry.title
        self.updated = to_date_time(entry.updated)
        self.links = Links(entry.link, repository)
        self.object = entry.object

class CMISFeedParser(object):
    """
    Couple of different feeds here. Service and Feed, we care mostly about feed.     
    """
    def __init__(self, response, repository):
        self.headers = response.headers
        self.feed = ConvertXmlToDict(ElementTree.fromstring(response.read()))
        self.repository = repository
    def parse(self):
        """
        Turns the Feed into a listing of Nodes
        """
        if self.feed.has_key('feed') and self.feed.feed.has_key('entry'):
            nodes = []
            for entry in self.feed.feed.entry:
                nodes.append(Node(entry, self.repository))
            return nodes
        elif self.feed.has_key('entry'):
            return Node(self.feed.entry, self.repository)
        else:
            return self.feed
    
    def parse_types(self):
        """
        Types are a pain to navigate in CMIS form. we create a better dict
        
        CMIS defines four root types:
            o Document object type
            o Folder object type
            o Relationship object type
            o Policy object type
        """
        rd = XmlDictObject()
        rd.document = []
        rd.folder = []
        rd.relationship = []
        rd.policy = []
        entries = self.feed.feed.entry
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            if entry.has_key('folderType'):
                t = entry.folderType
                del entry.folderType
                entry.options = t
                rd.folder.append(entry)
            elif entry.has_key('documentType'):
                t = entry.documentType
                del entry.documentType
                entry.options = t
                rd.document.append(entry)
            elif entry.has_key('relationshipType'):
                t = entry.relationshipType
                del entry.relationshipType
                entry.options = t
                rd.relationship.append(entry) 
            elif entry.has_key('policyType'):
                t = entry.policyType
                del entry.policyType
                entry.options = t
                rd.policy.append(entry)
        return rd

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
        
class CMISService(object):
    """
    Does makes the acutally request to CMIS
    
        c = CMISService()
        c.put('d47304b8-29f5-4379-9b52-0ae26cc665ca', 'TICKET_45fff4a178006140bc9f5c30a78b91ec092ad279', {'title': 'new folder 4'},)
        
        c.simple('TICKET_45fff4a178006140bc9f5c30a78b91ec092ad279', 'repository')
        Returns a dictionary. 
        
    TODO:
        Error handling.
    """
    def __init__(self, service_url='http://localhost:8080/', service_root='alfresco/service/api', user=None, password=None):
        self.service_url = service_url
        self.service_root = service_root
        self.url = None
        self.auth =  None
        #If we get a username and password we assume that it's the default user.
        if user and password:
            self.auth = self._authorize(user=user, password=password)
    
    def _authorize(self, **kwargs):
        user = kwargs.pop('user', None)
        password = kwargs.pop('password', None)
        ticket = kwargs.pop('ticket', None)
        #honor the passed in information first
        if ticket:
            return base64.encodestring(ticket).strip()
        elif user and password:
            return base64.encodestring('%s:%s' % (user, password)).strip()
        elif self.auth:
            return self.auth
        else:
            #Need CMIS specific Error
            raise TypeError('need either a ticket or a username and password')
    
    def _build_url(self, *args, **kwargs):
        self.url = join([self.service_url, self.service_root] + list(args))
        query = '&'.join(['%s=%s' % (key, value) for key, value in kwargs.items() if value is not None])
        if query:
            self.url = self.url +'?'+query.replace(' ', '%20')
        print self.url
    
    def get(self, id, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        auth = self._authorize( **kwargs)
        request = RESTRequest(self.url, method='GET', auth=auth)
        request_response = urllib2.urlopen(request)
        return request_response

    def simple(self, method, **kwargs):
        self._build_url(method, **kwargs)
        auth = self._authorize( **kwargs)
        request = RESTRequest(self.url, method='GET', auth=auth)
        request_response = urllib2.urlopen(request)
        return request_response
    
    def delete(self, id, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        auth = self._authorize( **kwargs)
        request = RESTRequest(self.url, method='DELETE', auth=auth)
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code is not 204:
                raise e
        return None
    
    def put(self, id, payload, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        auth = self._authorize( **kwargs)
        request = RESTRequest(self.url, payload, method='PUT', auth=auth)
        request.add_header('Content-Type', 'application/atom+xml;type=entry')
        request_response = urllib2.urlopen(request)
        return request_response
    
    def post(self, id, payload, method=None, package='node', store_type='workspace', store_id='SpacesStore', **kwargs):
        self._build_url(package, store_type, store_id, id, method, **kwargs)
        auth = self._authorize( **kwargs)
        request = RESTRequest(self.url, payload, method='POST', auth=auth)
        request.add_header('Content-Type', 'application/atom+xml;type=entry')
        try:
            urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            if e.code is not 201:
                raise e
            else:
                return e.read()

class Repository(object):
    """
    Main class for a CMIS Repository. Every function is scoped within a Repository.
    
    The function calls are based off the CMIS Rest protocol binding v.05 not the alfresco implementation
    
    """
    
    constants = {'VERSIONING_STATE' : 
                 {'CHECKED_OUT':'CheckedOut', 'CHECKED_IN_MINOR':'CheckedInMinor', 'CHECKED_IN_MAJOR':'CheckedInMajor'},
                 'INCLUDE_RELATIONSHIPS' : ['none', 'source', 'target', 'both']}
    
    def __init__(self, service_url, service_root, username, password):
        self.service = CMISService(service_url, service_root, username, password)
        feed = self.get_repository_info()
        #Only one workspace in Alfresco Repositories
        data = feed.service.workspace
        self.title = data.title
        self.id = data.repositoryInfo.repositoryId
        self.name = data.repositoryInfo.repositoryName
        self.relationship = data.repositoryInfo.repositoryRelationship
        self.description = data.repositoryInfo.repositoryDescription
        self.vendor_name = data.repositoryInfo.vendorName
        self.product_name = data.repositoryInfo.productName
        self.product_version = data.repositoryInfo.productVersion
        self.root_folder_id = data.repositoryInfo.rootFolderId
        self.collections = dict([(a.collectionType, a.href) for a in data.collection])
        self.capabilities = data.repositoryInfo.capabilities


    def execute(self, http_method, *args, **kwargs):
        """
        Executes Methods. Handles the parse and everything fun about it. 
        """

        func = getattr(self.service, http_method.lower())        
        response = func(*args, **kwargs)
        
        response_type = response.headers.subtype
        
        if response_type == 'atom+xml':
            return CMISFeedParser(response, self)
        else:
            return response.read()

    #REPOSITORY SERVICES
    def get_repositories(self, **kwargs):
        """
        GET /alfresco/service/api/repository
        GET /alfresco/service/api/cmis
        """
        raise NotImplementedError("Alfresco doesn't have multiple repositories")
    
    def get_repository_info(self, **kwargs):
        """
        getRepositoryInfo
        This service is used to retrieve information about the CMIS repository and the capabilities
        it supports.
        Headers: CMIS-repositoryId
        HTTP Arguments: repositoryId
        """
        return self.execute('simple', method='repository', **kwargs).feed

    def get_types(self, skipCount=0, maxItems=0, includePropertyDefinition=False, **kwargs):
        """
        GET /alfresco/service/api/types?type={type?}&includePropertyDefinitions={includePropertyDefinitions?}&skipCount={skipCount?}&maxItems={maxItems?}
        ---
        Returns the list of all types in the repository.
        
        Inputs:
        
        (Optional) ID typeId: not set (default)
        (Optional) Bool returnPropertyDefinitions: False (default)
        (Optional) int maxItems: 0 = Repository-default number of items (Default)
        (Optional) int skipCount: 0 = start (Default)
        
        Outputs:
        
        Result Set - List of types
        Boolean hasMoreItems
        The type attributes of each type will be returned
        The property definitions of each type will be returned if returnPropertyDefinitions is TRUE.
        
        Notes:
        
        A repository may support a hierarchy of types but CMIS will return them as a flat list.
        If provided, the input parameter "TypeId" specifies to only return the specific Object Type 
        and its descendants. If not provided, all Object Types are to be returned.
        
        If no "maxItems" value is provided, then the Repository will determine an appropriate number
        of items to return. How the Repository determines this value is repository-specific and opaque to CMIS.
        
        If "returnPropertyDefinitions" is False, then the Repository will return only the 
        "Attributes" of the Object Type Definition as specified in the "Object Type" section of the Data Model.
        Otherwise, property definitions will also be returned for each object type.
        ---
        """
        return self.execute('simple', method='types', skipCount=skipCount, maxItems=maxItems, 
                                includePropertyDefinition=includePropertyDefinition, **kwargs).parse_types()
    
    def get_type_definition(self, type, includePropertyDefinition=False, **kwargs):
        """
        getTypeDefinition
        
        Gets the definition for specified type
        
        Headers: CMIS-includePropertyDefinitions (Boolean)
        HTTP Arguments: includePropertyDefinitions
        """
        return self.execute('simple', method='types', type=type, 
                            includePropertyDefinition=includePropertyDefinition).parse_types()
    
    def get_allowable_actions(self):
        """
        getAllowableActions
        Description
            Returns the list of allowable actions for a document, folder, or relationship object based
            on thGET /alfresco/service/api/node/{store_type}/{store_id}/{id}?filter={filter?}&returnVersion={returnVersion?}
        GET /alfresco/service/api/path/{store_type}/{store_id}/{id}?filter={filter?}&returnVersion={returnVersion?}
        ---
        Returns the properties of an object, and optionally the operations that the user is allowed to perform on the object
        
        Inputs:
        
        ID objectId
        (Optional) Enum returnVersion: This (Default), Latest, LatestMajor
        (Optional) String filter: Filter for properties to be returned
        (Optional) Boolean includeAllowableActions: False (default)
        (Optional) Enum includeRelationships: none (default), source, target, both
        
        Outputs:
        
        Collection propertyCollection
        Collection allowableActionCollection
        
        Notes:
        
        If "includeAllowableActions" is TRUE, the repository will return the allowable actions for the current user for the object as part of the output.
        
        "IncludeRelationships" indicates whether relationships are also returned for the object. If it is set to "source" or "target", 
        relationships for which the returned object is a source, or respectively a target, will also be returned. If it is set to "both", 
        relationships for which the returned object is either a source or a target will be returned. If it is set to "none", relationships are not returned.
        
        Does not return the content-stream of a document
        PropertyCollection includes changeToken (if applicable to repository)
        e current user's context.
        """
        pass
    
    def get_properties(self):
        """
        getAllowableActions
        Description
            Returns the list of allowable actions for a document, folder, or relationship object based
            on th
        GET /alfresco/service/api/node/{store_type}/{store_id}/{id}?filter={filter?}&returnVersion={returnVersion?}
        GET /alfresco/service/api/path/{store_type}/{store_id}/{id}?filter={filter?}&returnVersion={returnVersion?}
        ---
        Returns the properties of an object, and optionally the operations that the user is allowed to perform on the object
        
        Inputs:
        
        ID objectId
        (Optional) Enum returnVersion: This (Default), Latest, LatestMajor
        (Optional) String filter: Filter for properties to be returned
        (Optional) Boolean includeAllowableActions: False (default)
        (Optional) Enum includeRelationships: none (default), source, target, both
        
        Outputs:
        
        Collection propertyCollection
        Collection allowableActionCollection
        
        Notes:
        
        If "includeAllowableActions" is TRUE, the repository will return the allowable actions for the current user for the object as part of the output.
        
        "IncludeRelationships" indicates whether relationships are also returned for the object. If it is set to "source" or "target", 
        relationships for which the returned object is a source, or respectively a target, will also be returned. If it is set to "both", 
        relationships for which the returned object is either a source or a target will be returned. If it is set to "none", relationships are not returned.
        
        Does not return the content-stream of a document
        PropertyCollection includes changeToken (if applicable to repository)
        e current user's context.
        """
        pass
        
    def update_properties(self):
        """
        PUT /alfresco/service/api/node/{store_type}/{store_id}/{id}
        PUT /alfresco/service/api/path/{store_type}/{store_id}/{id}
        ---
        This service updates properties of the specified object. As per the data model, content-streams are not properties
        
        Inputs:
        
        ID objectId
        (Optional) String changeToken
        Collection propertyCollection - Subset list of Properties to update
        
        Outputs:
        
        ID objectId
        
        Notes:
        
        Preserves the ID of the object
        Subset of properties: Properties not specified in this list are not changed
        To remove a property, specify property with no value
        If an attempt is made to update a read-only property, throw ConstraintViolationException.
        If a ChangeToken is provided by the repository when the object is retrieved, the change token MUST be included as-is when calling updateProperties.
        For Multi-Value properties, the whole list of values MUST be provided on every update.
        Use getAllowableActions to identify whether older version specified by ID is updatable.
        If this is a private working copy, some repositories may not support updates.
        Because repositories MAY automatically create new Document Versions on a user's behalf, the objectId returned may not match the one provided as an input to this method.
        """
        pass
    
    def delete_object(self):
        """
        DELETE /alfresco/service/api/node/{store_type}/{store_id}/{id}?includeChildren={includeChildren?}
        DELETE /alfresco/service/api/path/{store_type}/{store_id}/{id}?includeChildren={includeChildren?}
        ---
        Deletes specified object
        
        Inputs:
        
        ID objectId
        
        Notes:
        
        If the object is a Folder with at least one child, throw ConstraintViolationException.
        If the object is the Root Folder, throw OperationNotSupportedException.
        When a filed object is deleted, it is removed from all folders it is filed in.
        This service deletes a specific version of a document object. To delete all versions, use deleteAllVersions()
        Deletion of a private working copy (checked out version) is the same as to cancel checkout.
        ---
        """
        pass
    
    #FUNCTIONS THAT HAVE NOT BEEN CONFIRMED TO WORK
    def move_object(self):
        """
        Description
            Moves specified folder or document to new location
        Arguments
            Headers: CMIS-removeFrom (String)
            HTTP Arguments: removeFrom
        
        Post an entry doc to the new collection location.
        Header CMIS-removeFrom: folderId.
        Note: For repositories that do not support multi -filing, the item will always be removed from the previous folder,
        even if the header is not specified.
        """
        pass        
    def set_content_stream(self):
        """
        Description
            Sets (creates or replaces) the content stream for the version specified of a document
            object.
        This method follows the Atom Publishing model where the media (content stream) is PUT at the edit-media or
        stream link.
        
        TODO: No alfresco impl
        """
        raise NotImplementedError("Alfresco doesn't have this yet")
    
    def delete_content_stream(self):
        """
        Description 
            Deletes the content stream of the specified document Id. This does not delete properties.
            If there are other versions this does not affect them, their properties or content.
            This does not change the ID of the document.
        TODO: No alfresco impl
        """
        raise NotImplementedError("Alfresco doesn't have this yet")
    
    def add_document_to_folder(self):
        """
        Description 
            Adds an existing document object to a folder. This may fail based on repository rules such
            as multi-filing not being supported, documents only being allowed to be filed once in any
            folder, etc.
        Arguments   
            Headers: CMIS-removeFrom (String), CMIS-thisVersion (Boolean)
            HTTP Arguments: removeFrom, thisVersion
        """
        pass
    
    def remove_document_from_folder(self):
        """
        Description 
            Removes document from a folder. This does not delete the document and does not
            change the ID of the document.
        
        To remove the document from all folders: post it to the Unfiled collection.
        
        To remove the document from a particular folder: post an entry for the document to a folder in which you want
        the document to be filed, including the http header "CMIS-removeFrom" with the value set to the folder from
        which you want to unfile the document. (If the document is already in the folder to which you are posting, the
        document will be removed from the specified folder, but NOT doubly filed into the target folder.)
        """
        pass
    
    #VERSIONING SERVICES
    
    def get_properties_of_latest_version(self):
        """
        Description
            Returns the properties of the latest version, or the latest major version, of the specified
            version series
        Arguments
            Headers: CMIS-filter (Boolean), CMIS- majorVersion (Boolean)
            HTTP Arguments: filter, majorVersion
        
        This method is accessed by following the link of type 'cmis -latestversion' on any entry. The inputs will be HTTP
        header tags on the GET request.
    
        SEE getProperties
        """
        pass
    
    def get_all_versions(self):
        """
        Description 
            Returns the list of all members of the version series for the specified document, sorted by
            CREATION_DATE descending.
        Arguments   
            Headers: CMIS-filter (String)
            HTTP Arguments: filter
        """
        pass
    
    def delete_all_versions(self):
        """
        deleteAllVersions
        Description
            Deletes all documents in the version series specified by a member's ObjectId.
        This method will be invoked by calling DELETE on link 'cmis -allversions' resource.
        """
        pass
    
    def get_relationships(self):
        """
        Description 
            Returns a list of relationships associated with the object.
        Arguments
            Headers:
                CMIS-relationshipType (String), CMIS-includeSubRelationshipTypes (Boolean),
                CMIS-filter (String), CMIS-maxItems (Integer), CMIS-skipCount (Integer), CMIS-direction
                (enumRelationshipDirection), CMIS-includeAllowableActions (Boolean)
            HTTP Arguments: 
                relationshipType, includeSubRelationshipTypes, filter, maxResults,
                skipCount, direction (target, s ource, all) , includeAllowableActions
        """
        raise NotImplementedError("Alfresco doesn't have this yet")
 
    def create_relationship(self):
        """
        Description             
            Creates the object of the specified type
            This method follows the Atom Publishing model where the entry document is posted to the root or any other CMIS
            collection.
        """
        raise NotImplementedError("Alfresco doesn't have this yet")


        #NAVIGATION SERVICES
    def get_descendants(self, id=None, depth=1, types=None, filter=None, include_allowable_actions=False, 
                        include_relationships=None, order_by=None, package='node', **kwargs):
        """
        Description 
            Gets the list of document and folder objects contained at one or more levels below the
            specified folder. Only the selected properties associated with each object are returned.
            The content stream is not returned.
            This will return the version of the documents in the folder specified by the user filing the
            documents into the folder. Typically and by default this will be the latest version.
        Arguments   
            Headers: CMIS-childTypes (enumTypesOfFileableObjects), CMIS-filter (String), CMIS-depth
            (Integer), CMIS-includeAllowableActions (Boolean), CMIS-includeRelationships
            (enumIncludeRelationships), CMIS-folderByPath (String)
            
            GET /alfresco/service/api/node/{store_type}/{store_id}/{id}/descendants?types={types}&filter={filter?}&depth={depth?}
            GET /alfresco/service/api/path/{store_type}/{store_id}/{id}/descendants?types={types}&filter={filter?}&depth={depth?}
            ---
            Gets the list of descendant objects contained at one or more levels in the tree rooted at the specified folder. 
            Only the filter-selected properties associated with each object are returned. The content-stream is not returned.
            
            For paging through the children (depth of 1) only use getChildren. For returning a tree of objects of a certain depth, use getDescendants.
            
            For a repository that supports version-specific filing, this will return the version of the documents in the folder 
            specified by the user filing the documents into the folder. Otherwise, the latest version of the documents will be returned.
            
            Inputs:
            
            ID folderId
            (Optional) Enum type: Documents, Folders, Policies, Any (default)
            (Optional) Int depth: 1 this folder only (Default), N folders deep, -1 for all levels
            (Optional) String filter: Filter specifying which properties to return.
            (Optional) Boolean includeAllowableActions: False (default)
            (Optional) Enum includeRelationships: none (default), source, target, both
            (Optional) String orderBy: must be a valid ORDER BY clause from the query grammer excluding 'ORDER BY'. Example 'name DESC'.
            
            Outputs:
            
            Result set specified by Filter of each descendant object in the specified folder
            This result set will nest the contained objects
            
            Notes:
            
            The ordering and tree walk algorithm is repository-specific, but SHOULD be consistent.
            This method will return all objects of the specified type in the specified depth.
            If no type is specified, then objects of all types will be returned.
            When returning the results of a call where the caller specified "Any" type, the repository SHOULD return, at each nesting level,
            all folder objects first followed by other objects.
            If "includeAllowableActions" is TRUE, the repository will return the allowable actions for the current 
            user for each descendant object as part of the output.
            "IncludeRelationships" indicates whether relationships are also returned for each returned object. 
            If it is set to "source" or "target", relationships for which the returned object is a source, 
            or respectively a target, will also be returned. If it is set to "both", relationships for 
            which the returned object is either a source or a target will be returned. 
            If it is set to "none", relationships are not returned.

        """
        
        return self.execute('get', id=id, method='descendants', package=package, depth=depth, types=types, 
                      filter=filter, includeAllowableActions=include_allowable_actions, 
                      includeRelationships=include_relationships, orderBy=order_by, **kwargs).parse()
    
    def get_children(self, id=None, types=None, filter=None, include_allowable_actions=False, 
                        include_relationships=None, max_items=0, skip_count=0, order_by=None, package='node', **kwargs):
        """
        GET /alfresco/service/api/node/{store_type}/{store_id}/{id}/children?types={types}&filter={filter?}&skipCount={skipCount?}&maxItems={maxItems?}
        GET /alfresco/service/api/path/{store_type}/{store_id}/{id}/children?types={types}&filter={filter?}&skipCount={skipCount?}&maxItems={maxItems?}
        ---
        Gets the list of child objects contained in the specified folder. Only the filter-selected properties associated with each 
        object are returned. The content-streams of documents are not returned.
        
        For paging through the children (depth of 1) only use getChildren. For returning a tree of objects of a certain depth, use getDescendants.
        
        For a repository that supports version-specific filing, this will return the version of the documents in the folder specified 
        by the user filing the documents into the folder. Otherwise, the latest version of the documents will be returned.
        
        Inputs:
        
        ID folderId
        (Optional) Enum type: Documents, Folders, Policies, Any (default)
        (Optional) String filter: Filter specifying which properties to return.
        (Optional) Boolean includeAllowableActions: False (default)
        (Optional) Enum includeRelationships: none (default), source, target, both
        (Optional) int maxItems: 0 = Repository-default number of items (Default)
        (Optional) int skipCount: 0 = start (Default)
        (Optional) String orderBy: must be a valid ORDER BY clause from the query grammer excluding -ORDER BY-. Example -name DESC-.
        
        Outputs:
        
        Result set specified by Filter of each child object in the specified folder
        If maxItems > 0, Bool hasMoreItems
        
        Notes:
        
        Between invocations the order of the results may change due to repository state changing, i.e. skipCount might not show 
        objects or more likely show an object twice (bottom of first page and top of second) when an object is added to the top of the list.
        
        Ordering is repository-specific except the ordering MUST remain consistent across invocations, provided that the repository state has not changed.
        When returning the results of a call where the caller specified -Any- type, the repository SHOULD return all folder objects first followed by other objects.
        If includeAllowableActions is TRUE, the repository will return the allowable actions for the current user for each child object as part of the output.
        
        "IncludeRelationships" indicates whether relationships are also returned for each returned object. If it is set to "source" or "target", 
        relationships for which the returned object is a source, or respectively a target, will also be returned. If it is set to "both", 
        relationships for which the returned object is either a source or a target will be returned. If it is set to "none", relationships are not returned.
        
        If no maxItems value is provided, then the Repository will determine an appropriate number of items to return. 
        How the Repository determines this value is repository-specific and opaque to CMIS.
        ---
        """
        
        
        return self.execute('get', id=id, method='children', package=package, types=types, 
                      filter=filter, includeAllowableActions=include_allowable_actions, 
                      includeRelationships=include_relationships,  maxItems=max_items, 
                      skipCount=skip_count, orderBy=order_by, **kwargs).parse()

    
    def get_folder_parent(self):
        pass
    
    def get_checked_out_documents(self, id, filter=None, include_allowable_actions=False, 
                        include_relationships=None, max_items=0, skip_count=0, **kwargs):
        """
        GET /alfresco/service/api/checkedout?folderId={folderId?}&includeDescendants={includeDescendants?}&filter={filter?}&skipCount={skipCount?}&maxItems={maxItems?}
        ---
        Gets the list of documents that are checked out that the user has access to. Most likely this will be the set of documents checked out by the user. C
        ontent-streams are not returned.
        
        Inputs:
        
        (Optional) ID folderId
        (Optional) String filter specifying which properties to return.
        (Optional) Boolean includeAllowableActions: False (default)
        (Optional) Enum includeRelationships: none (default), source, target, both
        (Optional) int maxItems: 0 = Repository-default number of items (Default)
        (Optional) int skipCount: 0 (Default)
        
        Outputs:
        
        Result set specified by Filter
        Bool hasMoreItems
        
        Notes:
        
        The documents will be returned in a repository-specific order.
        The repository may include checked-out objects that the calling user has access to, but did not check out.
        If folderId is specified, then the results MUST include only the children of that folder, NOT other descendants of the folder 
        nor documents outside this tree.
        If "includeAllowableActions" is TRUE, the repository will return the allowable actions for the current user for each document as part of the output.
        
        "IncludeRelationships" indicates whether relationships are also returned for each returned object. If it is set to "source" or "target", 
        relationships for which the returned object is a source, or respectively a target, will also be returned. If it is set to "both", 
        relationships for which the returned object is either a source or a target will be returned. If it is set to "none", relationships are not returned.
        
        If no "maxItems" value is provided, then the Repository will determine an appropriate number of items to return. 
        How the Repository determines this value is repository-specific and opaque to CMIS.

        """
        return self.service.simple(method='checkedout', folderId=id,
                      filter=filter, includeAllowableActions=include_allowable_actions, 
                      includeRelationships=include_relationships,  maxItems=max_items, 
                      skipCount=skip_count, **kwargs)
    
    #OBJECT SERVICES
    def create_document(self, id, type, properties, folder_id=None, content_stream=None, versioning_state=None, package='node', **kwargs):
        """
        POST /alfresco/service/api/node/{store_type}/{store_id}/{id}/children
        POST /alfresco/service/api/path/{store_type}/{store_id}/{id}/children
        ---
        Creates a document object of the specified type, and optionally adds the document to a folder
        
        Inputs:
        
        ID typeId: Document type
        Collection properties
        (Optional) ID folderId: Parent folder for this new document
        (Optional) ContentStream contentStream
        (Optional) Enum versioningState: CheckedOut, CheckedInMinor, CheckedInMajor (Default)
        
        Outputs:
        
        ID objectId: Id of the created document object
        
        The versioningState input is used to create a document in a checked-out state, or as a checked-in minor version, 
        or as a checked-in major version. If created in a checked-out state, the object is a PWC and there is no corresponding 
        "checked out document". (See the "Versioning" section.)
        
        If the Document's Object Type does not allow content-stream and a content-stream is provided, or if content-stream is 
        required and a content-stream is not provided, throw ConstraintViolationException.
        If a Folder is specified, and the Document's Object Type is not one of the "Allowed_Child_Object_Types" for this Folder, 
        throw ConstraintViolationException.
        If unfiling is not supported and a Folder is not specified, throw FolderNotValidException.
        Repositories MAY reject the createDocument request (by throwing ConstaintViolationException) 
        if any of the Required properties specified in the Document's Object Type are not set.
        However, iF the repository does NOT reject the createDocument request in this case, the repository MUST leave 
        the newly-created Document in a checked-out state, and MUST ensure that all required properties are set 
        before the Document is checked in.
        
        Creates a folder object of the specified type
        
        <?xml version="1.0" encoding="utf-8"?>
        <entry xmlns="http://www.w3.org/2005/Atom" xmlns:cmis="http://www.cmis.org/2008/05">
            <title>${NAME}</title>
            <summary>${NAME} (summary)</summary>
            <content type="text/html">${CONTENT}</content>
            <cmis:object>
                <cmis:properties>
                    <cmis:propertyString cmis:name="ObjectTypeId"><cmis:value>document</cmis:value></cmis:propertyString>
                </cmis:properties>
            </cmis:object>
        </entry>
        Inputs:
        
        ID typeId: Folder type
        Collection properties
        ID folderId: Parent folder for this new folder
        
        Outputs:
        
        ID objectId: Id of the created folder object
        
        Notes:
        If the to-be-created Folder's Object Type is not one of the "Allowed_Child_Object_Types" for the parent Folder, throw ConstraintViolationException.
        Root folder can not be created using this service.
        """
        pass
    
    def create_folder(self):
        """
        POST /alfresco/service/api/node/{store_type}/{store_id}/{id}/children
        POST /alfresco/service/api/path/{store_type}/{store_id}/{id}/children
        ---
        Creates a document object of the specified type, and optionally adds the document to a folder
        
        Inputs:
        
        ID typeId: Document type
        Collection properties
        (Optional) ID folderId: Parent folder for this new document
        (Optional) ContentStream contentStream
        (Optional) Enum versioningState: CheckedOut, CheckedInMinor, CheckedInMajor (Default)
        
        Outputs:
        
        ID objectId: Id of the created document object
        
        The versioningState input is used to create a document in a checked-out state, or as a checked-in minor version, 
        or as a checked-in major version. If created in a checked-out state, the object is a PWC and there is no corresponding 
        "checked out document". (See the "Versioning" section.)
        
        If the Document's Object Type does not allow content-stream and a content-stream is provided, or if content-stream is 
        required and a content-stream is not provided, throw ConstraintViolationException.
        If a Folder is specified, and the Document's Object Type is not one of the "Allowed_Child_Object_Types" for this Folder, 
        throw ConstraintViolationException.
        If unfiling is not supported and a Folder is not specified, throw FolderNotValidException.
        Repositories MAY reject the createDocument request (by throwing ConstaintViolationException) 
        if any of the Required properties specified in the Document's Object Type are not set.
        However, iF the repository does NOT reject the createDocument request in this case, the repository MUST leave 
        the newly-created Document in a checked-out state, and MUST ensure that all required properties are set 
        before the Document is checked in.
        
        Creates a folder object of the specified type
        
        Inputs:
        
        ID typeId: Folder type
        Collection properties
        ID folderId: Parent folder for this new folder
        
        Outputs:
        
        ID objectId: Id of the created folder object
        
        Notes:
        If the to-be-created Folder's Object Type is not one of the "Allowed_Child_Object_Types" for the parent Folder, throw ConstraintViolationException.
        Root folder can not be created using this service.
        """
        pass

    def delete_tree(self):
        """
        DELETE /alfresco/service/api/node/{store_type}/{store_id}/{id}/descendants?continueOnFailure={continueOnFailure?}&unfileMultiFiledDocuments={unfileMultiFiledDocuments}
        DELETE /alfresco/service/api/path/{store_type}/{store_id}/{id}/descendants?continueOnFailure={continueOnFailure?}&unfileMultiFiledDocuments={unfileMultiFiledDocuments}
        ---
        Deletes the tree rooted at specified folder (including that folder)
        
        Inputs:
        
        ID folderId
        Enum unfileNonfolderObjects:
        o Unfile -- unfile all non-folder objects from folders in this tree. They may remain filed in other folders, or may become unfiled.
        o DeleteSingleFiled -- delete non-folder objects filed only in this tree, and unfile the others so they remain filed in other folders.
        o Delete -- delete all non-folder objects in this tree (Default)
        (Optional) Bool continueOnFailure: False (Default)
        
        Outputs:
        
        Collection failedToDelete - List of object IDs that failed to delete (if continueOnFailure is FALSE, then single object ID)
        
        Notes:
        
        If a non-folder object is removed from the last folder it is filed in, it can continue to survive outside of the folder 
        structure if the repository supports the "Unfiling" capabiliity.
        If the specified folder is the Root Folder, throw OperationNotSupportedException.
        If unfiling is not supported, throw OperationNotSupportedException if deleteTree is called with Unfile.
        For repositories that support version-specific filing, this may delete some versions of a document but not necessarily 
        all versions. For repositories that do not support version-specific filing, if a document is to be deleted, all versions are deleted.
        This is not transactional.
        o However, if DeleteSingleFiled is chosen, then having the objects unfiled is not sufficient if some objects fail to delete. 
        The user MUST be able to re-issue command (recover) from the error by using the same tree.
        Does not specify the order in which delete will happen
        o However, any objects that are not deleted (e.g. because a previous object failed to delete), they MUST remain valid CMIS objects 
        (including any applicable filing constraint for each object).
        ---
        """
        pass

    def get_object_parents(self, id=None, filter=None, include_allowable_actions=False, 
                        include_relationships=None, package='node', **kwargs):
        """
        GET /alfresco/service/api/node/{store_type}/{store_id}/{id}/parents?filter={filter?}
        GET /alfresco/service/api/path/{store_type}/{store_id}/{id}/parents?filter={filter?}
        ---
        Returns the parent folders for the specified non-folder, fileable object
        
        Inputs:
        
        ID objectId: ID of a non-folder, fileable object.
        (Optional) String filter: filter specifying which properties to return.
        (Optional) Boolean includeAllowableActions: False (default)
        (Optional) Enum includeRelationships: none (default), source, target, both
        
        Outputs:
        
        ResultSet resultSet - Set of folders containing the object.
        
        Notes:
        
        Order is repository-specific
        It is suggested that the parent and the ObjectId properties are included in the filter to allow re-ordering if necessary.
        If "includeAllowableActions" is TRUE, the repository will return the allowable actions for the current user for each parent folder as part of the output.
        "IncludeRelationships" indicates whether relationships are also returned for each returned object. If it is set to "source" or "target", relationships for which the returned object is a source, or respectively a target, will also be returned. If it is set to "both", relationships for which the returned object is either a source or a target will be returned. If it is set to "none", relationships are not returned.     
        """
        return self.service.get(id=id, method='parents', package=package,
              filter=filter, includeAllowableActions=include_allowable_actions, 
              includeRelationships=include_relationships, **kwargs)
    
    def cancel_check_out(self):
        """
        DELETE /alfresco/service/api/pwc/{store_type}/{store_id}/{id}
        ---
        Reverses the effect of a check-out. Removes the private working copy of the checked-out document object, allowing other documents in the version series to be checked out again.
        
        Inputs:
        
        ID documentId: ObjectId of Private Working Copy (ID returned on CheckOut)
        
        Notes:
        
        It is repository specific on who can cancel a checkout (user, admin, larger group, etc)
        Throws OperationNotSupportedException if the object is not checked out
        """
        pass
    
    def check_in(self):
        """
        PUT /alfresco/service/api/pwc/{store_type}/{store_id}/{id}?checkinComment={checkinComment?}&major={major?}&checkin={checkin?}
        ---
        Makes the private working copy the current version of the document.
        
        Inputs:
        
        ID documentId: ObjectId of the private working copy
        Optional) Boolean major: True (Default)
        (Optional) Property bag
        (Optional) ContentStream stream
        (Optional) String CheckinComment
        
        Outputs:
        
        ID documentId: ID for the new version of the document.
        
        Notes:
        
        It is left to the repository to determine who can check-in a document.
        CheckinComment is persisted if specified.
        For repositories that do not support updating private working copies, all updates MUST be set on the check-in service.
        If Document is not checked out, throw OperationNotSupportedException.
        If the Document has "Content_Stream_Allowed" set to FALSE, and a call is made to checkIn that includes a content-stream, throw ConstraintViolationException.
        ---
        """
        pass
    
    def get_content_stream(self):
        """
        GET /alfresco/service/api/node/content{property}/{store_type}/{store_id}/{id}?a={attach?}
        GET /alfresco/service/api/path/content{property}/{store_type}/{store_id}/{id}?a={attach?}
        GET /alfresco/service/api/avmpath/content{property}/{store_id}/{id}?a={attach?}
        GET /alfresco/service/api/node/{store_type}/{store_id}/{id}/content{property}?a={attach?}
        GET /alfresco/service/api/path/{store_type}/{store_id}/{id}/content{property}?a={attach?}
        ---
        The service returns the content-stream for a document. This is the only service that returns content-stream.
        
        Inputs:
        
        ID documentId: Document to return the content-stream
        (Optional) Integer offset:
        (Optional) Integer length:
        
        Outputs:
        
        Byte[] stream
        
        Notes:
        
        Some CMIS protocol bindings MAY choose not to explicitly implement a "getContentStream" method, in cases where the protocol itself provides built-in mechanisms for retrieving byte streams. (E.g. in the ATOM/REST binding, content streams may be retrieved via standard HTTP gets on an "edit-media" URL, rather than a CMIS-specific "getContentStream" URL). See Part II of the CMIS specification for additional details.
        Each CMIS protocol binding will provide a way for fetching a sub-range within a content stream, in a manner appropriate to that protocol.
        ---
        """
        pass
    
        #DISCOVERY SERVICES
    def query(self):
        """
        Description 
            Queries the repository for folders and content based on properties or an optional full text
            string. Query returns version that matches the constraints of a content object and does
            not search relationship objects. The content stream is not returned as part of query.
        
        POST /alfresco/service/api/query
        ---
        Queries the repository for queryable object based on properties or an optional full-text string. Relationship objects are not queryable. Content-streams are not returned as part of query.
        
        Inputs:
        
        String statement: Query statement
        (Optional) Bool searchAllVersions: False (Default)
        (Optional) Boolean includeAllowableActions: False (default)
        (Optional) Enum includeRelationships: none (default), source, target, both
        (Optional) int maxItems: 0 = Repository-default number of items (Default)
        (Optional) int skipCount: 0 = Start at first position (Default)
        
        Outputs:
        
        Collection objectCollection - this collection represents a result table produced by the query statement. Typically each row of this table corresponds to an object, and each column corresponds to a property or a computed value as specified by the SELECT clause of the query statement. A CMIS SQL 1.0 query without JOIN always produces one object per row.
        Bool hasMoreItems
        
        Notes:
        
        If SearchAllVersions is True, and CONTAINS() is used in the query, OperationNotSupported will be thrown if full-text search is not supported or if the repository does not have previous versions in the full-text index.
        Returns set of objects from (skipCount, maxItems+skipCount)
        If no "maxItems" value is provided, then the Repository will determine an appropriate number of items to return. How the Repository determines this value is repository-specific and opaque to CMIS.
        If "includeAllowableActions" is TRUE, the repository will return the allowable actions for the current user for each result object in the output table as an additional multi-valued column containing computed values of type string, provided that each row in the output table indeed corresponds to one object (which is true for a CMIS SQL 1.0 query without JOIN).
        If each row in the output table does not correspond to a specific object and "includeAllowableActions" is TRUE, then InvalidArgumentException will be thrown.
        It is recommended that "includeAllowableActions" be used with query statements without JOIN, and that the Object ID property or "*" be included in the SELECT list.
        "IncludeRelationships" indicates whether relationships are also returned for each returned object. If it is set to "source" or "target", relationships for which the returned object is a source, or respectively a target, will also be returned. If it is set to "both", relationships for which the returned object is either a source or a target will be returned. If it is set to "none", relationships are not returned.
        ---
        """
        pass