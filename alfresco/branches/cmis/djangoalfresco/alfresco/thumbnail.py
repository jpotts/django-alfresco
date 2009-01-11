"""
Thumbnailing

Every piece of content needs to know what it's images look like. 

During the deserialization process we will be parsing the content for images and attaching those to the model.

The image wrapper below will take care of some of the niceties.

structure:
    alfresco/
        images/
            thumbnails/
                medium/
                    {id}.jpg
                imgpreview/
                    {id}.jpg
                etc...
"""
import urllib2
import re
import os
from BeautifulSoup import BeautifulSoup

from django.utils.functional import curry
from log.loggers import logger

from alfresco.settings import ALFRESCO_SERVICE_URL, ALFRESCO_THUMBNAIL_SIZES, ALFRESCO_LOCAL_THUMBNAIL_URL, ALFRESCO_LOCAL_THUMBNAIL_ROOT
from django.conf import settings

ALFRESCO_IMAGE_RE = re.compile('^/alfresco/d/d/workspace/SpacesStore/(?P<id>[-\w]+)/(?P<name>[-\w]+).(?P<extension>[-\w]+)$')

class ImageWrapper(object):
    """
    Wrapper around an image that gives us all the images urls
    
    """
    def __init__(self, url, id, name, extension, ticket=None):
        self.url = url
        self.id = id
        self.name = name
        self.extension = extension
        self.ticket = ticket
        self.thumbnails = {}
        self._get_images()
            
    def local_path(self, size):
        return '%s/%s.%s' % (size, self.id, self.extension)
    
    def local_file_path(self, size):
        return ALFRESCO_LOCAL_THUMBNAIL_ROOT + self.local_path(size)
        
    def local_file_folder_path(self, size):
        return ALFRESCO_LOCAL_THUMBNAIL_ROOT + '%s/' % size
    
    def get_image_url(self):
        return settings.MEDIA_URL + 'alfresco/images/%s.%s' % (self.id, self.extension)
        
    def create_thumbnail(self, size):
        """
        Really simple wrapper around getting a thumbnail from Alfresco.
        
        No real error handing because we want to fail silently to not break other things. 
        We will log though
        """
        
        url = ALFRESCO_SERVICE_URL + 'api/node/workspace/SpacesStore/%s/content/thumbnails/%s?c=force&alf_ticket=%s' % (self.id, size, self.ticket)
        try:
            request = urllib2.Request(url)
            request_response = urllib2.urlopen(request)
            try:
                os.makedirs(self.local_file_folder_path(size))
            except:
                pass
            f = open(self.local_file_path(size), 'w')
            f.write(request_response.read())
            f.close()
            self.thumbnails[size] = self._get_thumbnail_SIZE_url(self, size)
            logger.info('Thumbnail of size %s was created for image %s with an id of %s' % (size, self.name, self.id))
        except Exception, e:
            logger.error('Failed to create Thumbnail of size %s for image %s with an id of %s. Exception %s. url: %s'
                          % (size, self.name, self.id, str(e), url))

    def _get_thumbnail_SIZE_url(self, size):
        return ALFRESCO_LOCAL_THUMBNAIL_URL + self.local_path(size)
    
    def _get_images(self):
        from alfresco.service import SpaceStore
        #Get full size
        try:
            ss = SpaceStore(self.ticket, '%s/%s.%s' %(self.id, self.name, self.extension))
            ss.get()
        except Exception, e:
            logger.error('Failed to download image %s with an id of %s. Exception %s'
                          % (self.name, self.id, str(e)))
        #Thumbnails
        for size in ALFRESCO_THUMBNAIL_SIZES:
            file_path = ALFRESCO_LOCAL_THUMBNAIL_ROOT + self.local_path(size)
            if os.path.exists(file_path):
                continue
            self.create_thumbnail(size)
            

def parse_html_for_images(html, ticket=None):
    """
    Takes a piece of HTML content and a ticket. It will parse the story for images, download them locally and create thumbnails
    
    <img src="/alfresco/d/d/workspace/SpacesStore/c6a26694-37cf-4c52-ae02-be83223315fa/ainsley_1.jpeg"/>
    """
    iws = []
    soup = BeautifulSoup(html)
    images = soup.findAll('img')
    for image in images:
        ss_url = image.get('src')
        match = ALFRESCO_IMAGE_RE.match(ss_url)
        if match:
             id, name, extension = match.groups()
             iw = ImageWrapper(ss_url, id, name, extension, ticket)
             image['src'] = iw.get_image_url()
             iws.append(iw)
    return str(soup), iws